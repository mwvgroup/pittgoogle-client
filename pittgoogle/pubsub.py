#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""Consumer class to pull and process alerts from Pitt-Google's Pub/Sub streams."""

from dataclasses import dataclass
import logging
import os
from typing import (
    Any,
    ByteString,
    Callable,
    Dict,
    List,
    Tuple,
    NamedTuple,
    Optional,
    Union,
)

# from concurrent.futures.thread import ThreadPoolExecutor
from google.api_core.exceptions import NotFound
from google.cloud import pubsub_v1

# from google.cloud.pubsub_v1.subscriber.scheduler import ThreadScheduler
import queue

from .auth import Auth, AuthSettings
from .types import PittGoogleProjectIds
from .utils import avro_to_dict, class_defaults


LOGGER = logging.getLogger(__name__)


class Alert(NamedTuple):
    """Container for an alert delivered via a Pub/Sub message.

    Attributes:
        dict:
            Alert data as a dictionary.
        bytes:
            Alert data as bytes, as delivered by Pub/Sub.
        metadata:
            The Pub/Sub message's metadata and custom attributes.
        msg:
            The full Pub/Sub message containing this alert.
    """

    dict: Optional[Dict] = None
    bytes: Optional[ByteString] = None
    metadata: Optional[Dict] = None
    msg: Optional[pubsub_v1.types.PubsubMessage] = None


class Response(NamedTuple):
    """Response to be returned by a user callback.

    Attributes:
        ack:
            Whether to acknowledge the message. In general, this should be True if the
            message was processed successfully, and False if an error was encountered.
            If False, the message will remain in the subscription and be redelivered at
            a later time.

        result:
            Any object the user wishes to return after processing the alert.
            This will be handled by a `Consumer` as follows:

                - None:
                    This is the recommended value, if the user_callback ran
                    successfully. This value
                    will NOT be stored in `Consumer().results`, but the message
                    WILL be counted against `Consumer().flow_configs.max_results`.
                    The assumption is that the user_callback saved any results that
                    need to be persisted.

                - False:
                    This option allows the user to drop messages that do not pass a
                    custom filter. This value
                    will NOT be stored in `Consumer().results`, and the message
                    will NOT be counted against `Consumer().flow_configs.max_results`.

                - Any other value:
                    WILL be stored in `Consumer().results`, and the message
                    WILL be counted against `Consumer().flow_configs.max_results`.
    """

    ack: bool = True
    result: Any = None


@dataclass
class CallbackKwargs:
    """Keyword args used by a callback function/method while processing an alert.

    Attributes:
        user_callback:
            Callable provided by the user. It should accept a single `Alert` as input
            and return a `Response`.
        include:
            This tuple should contain the names of all `Alert` attributes that the user
            wants available to the callbacks.
    """

    user_callback: Optional[Callable[[Alert], Response]] = None
    include: Tuple[str] = tuple(["dict"])


@dataclass
class FlowConfigs:
    """Stopping conditions and flow control settings for a streaming pull."""

    def __init__(
        self,
        max_results: Optional[int] = 10,
        timeout: Optional[int] = 30,
        max_backlog: int = 1000,
    ):
        self._max_results = max_results
        self._timeout = timeout
        self._max_backlog = max_backlog

    @staticmethod
    def _basic_clean(key, value) -> Optional[int]:
        """Return `value` if passes basic validity checks, else return class default.

        Validity check: `value` must be either a positive integer or None.
        """
        default = class_defaults(FlowConfigs)[key]

        # check for None
        if value is None:
            return value

        # check for a positive integer
        else:
            try:
                int(value)
                assert value > 0

            # value is not valid, log warning and return default
            except (ValueError, AssertionError):
                LOGGER.warning(
                    (
                        f"Received invalid flow config {key}: {value}. "
                        f"Falling back to default {key}: {default}."
                    )
                )
                return default

            else:
                return int(value)

    # max_results
    @property
    def max_results(self) -> Optional[int]:
        """Maximum number of messages to pull.

        Default = 10, use None for no limit.
        """
        self._max_results = FlowConfigs._basic_clean("max_results", self._max_results)
        return self._max_results

    @max_results.setter
    def max_results(self, value):
        self._max_results = value

    @max_results.deleter
    def max_results(self):
        self._max_results = class_defaults(self)["max_results"]

    # timeout
    @property
    def timeout(self) -> Optional[int]:
        """Maximum number of seconds to wait for a new message before stopping.

        Default = 30. Use None for no limit.
        """
        return FlowConfigs._basic_clean("timeout", self._timeout)

    @timeout.setter
    def timeout(self, value):
        self._timeout = value

    @timeout.deleter
    def timeout(self):
        self._timeout = class_defaults(self)["timeout"]

    # max_backlog
    @property
    def max_backlog(self) -> int:
        """Maximum number of pulled but unprocessed messages before pausing the pull.

        Default = min(1000, `max_results`).
        Will be cleaned to satisfy `max_backlog <= max_results`.
        """
        max_backlog = FlowConfigs._basic_clean("max_backlog", self._max_backlog)

        # check specific validity conditions. upon failure, fall back to default value
        default = class_defaults(self)["max_backlog"]

        # max_backlog cannot be None
        if max_backlog is None:
            LOGGER.warning(f"max_backlog cannot be None. Using the default {default}.")
            max_backlog = default

        # be conservative, ensure max_backlog <= max_results
        try:
            assert max_backlog <= self.max_results

        except AssertionError:
            LOGGER.warning(
                (
                    "max_backlog > max_results. "
                    "This can result in an excessive number of pulled messages that will "
                    "never be processed. "
                    "Setting max_backlog = max_results."
                )
            )
            max_backlog = self.max_results

        except TypeError:
            # max_results is None, so accept any max_backlog
            pass

        self._max_backlog = max_backlog
        return self._max_backlog

    @max_backlog.setter
    def max_backlog(self, value):
        self._max_backlog = value

    @max_backlog.deleter
    def max_backlog(self):
        self._max_backlog = class_defaults(self)["max_backlog"]


@dataclass
class Topic:
    """Basic attributes of a Pub/Sub topic.

    Attributes:
        name:
            Name of the Pub/Sub topic.
        projectid:
            The topic owner's Google Cloud project ID. Pitt-Google's IDs can be
            obtained using `PittGoogleProjectIds().production`,
            `PittGoogleProjectIds().testing`, etc.
    """

    name: str = "ztf-loop"
    projectid: str = PittGoogleProjectIds().production

    @property
    def path(self) -> str:
        """Fully qualified path to the topic."""
        return f"projects/{self.projectid}/topics/{self.name}"

    @path.setter
    def path(self, value):
        _, self.projectid, _, self.name = value.split("/")
        LOGGER.info(f"Topic set to {self}")


@dataclass
class SubscriberClient:
    """Wrapper for a `pubsub_v1.SubscriberClient`.

    Initialization is idempotent for caller convenience.
    """

    def __init__(self, auth: Union[Auth, AuthSettings, "SubscriberClient"]):
        # initialization should be idempotent
        # unpack auth settings to attributes
        for name, val in auth.__dict__.items():
            setattr(self, name, val)

        # initialize attributes if not present in auth
        self._auth = getattr(self, "_auth", auth)
        self._client = getattr(self, "_client", None)

    # authentication
    @property
    def auth(self) -> Auth:
        """Class wrapper for `pittgoogle.auth.Auth` object.

        If this is set to a `pittgoogle.auth.AuthSettings` it will be used to
        instantiate an `Auth`, which will then replace it.

        The API call triggering authentication with Google Cloud is not made until
        the either the `auth.credentials` or `auth.session` attribute is explicitly
        requested.

        Settings this manually will trigger reinstantiation of `self.client`.
        """
        if self._auth is None:
            # just warn and return
            LOGGER.warning(
                (
                    "No auth.AuthSettings or auth.Auth supplied. "
                    "Cannot connect to Google Cloud."
                )
            )

        else:
            # make sure we have an Auth and not just an AuthSettings
            self._auth = Auth(self._auth)

        return self._auth

    @auth.setter
    def auth(self, value):
        self._auth = value
        # force reset of other attributes
        self.client = None

    @auth.deleter
    def auth(self):
        self._auth = None
        # force reset of other attributes
        self.client = None

    # client
    @property
    def client(self) -> pubsub_v1.SubscriberClient:
        """Class wrapper for a `pubsub_v1.SubscriberClient` object.

        The client is authenticated using `self.auth.credentials`.
        """
        if self._client is None:
            self._client = pubsub_v1.SubscriberClient(credentials=self.auth.credentials)
        return self._client

    @client.setter
    def client(self, value):
        self._client = value

    @client.deleter
    def client(self):
        self._client = None


@dataclass
class Subscription:
    """Basic attributes of a Pub/Sub subscription plus methods to administer it."""

    def __init__(
        self,
        name: str = "ztf-loop",
        client: Union[SubscriberClient, Auth, AuthSettings, None] = None,
        topic: Optional[Topic] = None,
    ):
        self._name = name
        self._client = client
        self._topic = topic
        self._projectid = None

    # name
    @property
    def name(self) -> str:
        """Name of the subscription."""
        if self._name is None:
            default = class_defaults(self)["name"]
            LOGGER.warning(f"No subscription name provided. Falling back to {default}.")
            self._name = default

        return self._name

    @name.setter
    def name(self, value):
        self._name = value

    @name.deleter
    def name(self):
        self._name = None

    # projectid
    @property
    def projectid(self) -> str:
        """Subscription owner's Google Cloud project ID."""
        if self._projectid is None:

            # get it from the client, if present
            if self._client is not None:
                self._projectid = getattr(self.client, "GOOGLE_CLOUD_PROJECT")
                LOGGER.debug(
                    f"Subscription's projectid obtained from client. {self._projectid}"
                )

            # get it from an environment variable
            else:
                self._projectid = os.getenv("GOOGLE_CLOUD_PROJECT", None)
                LOGGER.debug(
                    (
                        "Subscription's projectid obtained from environment variable. "
                        f"projectid = {self._projectid}"
                    )
                )

        return self._projectid

    @projectid.setter
    def projectid(self, value):
        self._projectid = value

    @projectid.deleter
    def projectid(self):
        self._projectid = None

    @property
    def path(self) -> str:
        """Fully qualified path to the subscription."""
        if self.projectid is None:
            LOGGER.warning(
                (
                    "Unable to construct the subscription path since the "
                    "projectid cannot be determined."
                )
            )
        return f"projects/{self.projectid}/subscriptions/{self.name}"

    # client
    @property
    def client(self) -> Optional[SubscriberClient]:
        """Class wrapper for a `SubscriberClient`.

        If this is set to a `pittgoogle.auth.Auth` or `pittgoogle.auth.AuthSettings`
        it will be used to instantiate a `SubscriberClient`, which will then replace it.

        This will be required in order to connect to the subscription,
        but the connection is not checked during instantiation.
        """
        if self._client is None:
            # nothing to do but warn
            LOGGER.warning("Cannot create a SubscriberClient.")

        else:
            # make sure we have a SubscriberClient and not just an Auth or AuthSettings
            self._client = SubscriberClient(self._client)

        return self._client

    @client.setter
    def client(self, value):
        self._client = value

    @client.deleter
    def client(self):
        self._client = None

    # topic
    @property
    def topic(self) -> Topic:
        """Class wrapper for a `Topic` that the subscription is or will be attached to.

        If the subscription exists this will be set to the topic that it is attached to.

        If the subscription needs to be created it will be attached to this topic.
        If this is None it will fallback to the name of the subscription and the default
        Pitt-Google project ID.
        """
        if self._topic is None:
            default = Topic(self.name)
            LOGGER.debug(f"No topic provided. Falling back to {default}.")
            self._topic = default

        return self._topic

    @topic.setter
    def topic(self, value):
        self._topic = value

    @topic.deleter
    def topic(self):
        self._topic = None

    # touch, create, and delete
    def touch(self) -> None:
        """Make sure the subscription exists and the client can connect.

        If the subscription does not exist, try to create.

        Note that messages published before a subscription is created are not available.
        """
        try:
            # check if subscription exists
            subscrip = self.client.client.get_subscription(subscription=self.path)

        except NotFound:
            self._create()

        else:
            LOGGER.info(
                (
                    f"Subscription exists: {self.path}\n"
                    f"Connected to topic: {self.topic.path}"
                )
            )
            self.topic.path = subscrip.topic

    def _create(self) -> None:
        """Try to create the subscription."""
        LOGGER.info(
            (
                f"Attempting to create subscription {self.path} "
                f"attached to topic {self.topic.path}."
            )
        )

        try:
            self.client.client.create_subscription(
                name=self.path, topic=self.topic.path
            )
        except NotFound:
            # suitable topic does not exist in the Pitt-Google project
            raise ValueError(
                (
                    "Subscription cannot be created because the topic "
                    f"{self.topic.name} does not seem to exist in the Google Cloud "
                    f"project {self.topic.projectid}. "
                    "Try connecting to a different topic."
                )
            )
        else:
            LOGGER.info(
                (
                    f"Created subscription: {self.path}\n"
                    f"Connected to topic: {self.topic.path}"
                )
            )

    def delete(self) -> None:
        """Delete the subscription."""
        try:
            self.client.client.delete_subscription(subscription=self.path)
        except NotFound:
            LOGGER.debug(
                (
                    f"Subscription {self.path} cannot be deleted because "
                    "it does not seem to exist."
                )
            )
        else:
            LOGGER.info(f"Deleted subscription: {self.path}")


@dataclass
class ConsumerSettings:
    """Settings for a `Consumer()` instance.

    Attributes:
        client:
            Either a `SubscriberClient` or the `Auth` or `AuthSettings` necessary
            to create one. This will be required in order to connect to the
            subscription, but the connection is not checked during instantiation.

        subscription:
            Pub/Sub subscription to be pulled.

        flow_configs:
            Stopping conditions and flow control settings for the streaming pull.

        callback_kwargs:
            Keyword arguments that will be available to the callbacks.
            These dictate the message delivery format, processing logic, and data
            returned.
            The callbacks include a `Consumer` object's self.callback and the
            user_callback (optionally) included this `callback_kwargs` object.
    """

    client: Union[SubscriberClient, Auth, AuthSettings] = AuthSettings()
    subscription: Union[str, Subscription] = "ztf-loop"
    flow_configs: FlowConfigs = FlowConfigs()
    callback_kwargs: CallbackKwargs = CallbackKwargs()


@dataclass
class Consumer:
    """Consumer class to pull a Pub/Sub subscription and process messages.

    Args:
        settings:
            A `ConsumerSettings` object. These are unpacked and set as attributes on
            `self`.

    Initialization does the following:
        - Authenticate the client to Google Cloud.
        - Touch the subscription, creating it if necessary.
    """

    def __init__(self, settings: ConsumerSettings):
        LOGGER.debug(
            f"Instantiating consumer with the following settings: {settings.__repr__()}"
        )

        # unpack consumer settings to attributes
        self._client = settings.client
        self._subscription = settings.subscription
        self.flow_configs = settings.flow_configs
        self.callback_kwargs = settings.callback_kwargs

        # authenticate and store credentials
        self.client.auth.credentials
        self.projectid = self.client.auth.GOOGLE_CLOUD_PROJECT

        # check connection to the subscription
        if self._subscription._client is None:
            self._subscription._client = self._client
        self.subscription.touch()

        # list of results of user processing. stored and returned upon user request
        self.results = []

        # instantiate a queue to communicate with the background thread
        self.__queue = None

    # subscriber client
    @property
    def client(self) -> Optional[SubscriberClient]:
        """Class wrapper for a `SubscriberClient`.

        If this is set to a `pittgoogle.auth.Auth` or `pittgoogle.auth.AuthSettings`
        it will be used to instantiate a `SubscriberClient`, which will then replace it.
        """
        if self._client is None:
            # nothing to do but warn
            LOGGER.warning("Cannot create a SubscriberClient.")

        else:
            # make sure we have a SubscriberClient and not just an Auth or AuthSettings
            self._client = SubscriberClient(self._client)

        return self._client

    @client.setter
    def client(self, value):
        self._client = value

    @client.deleter
    def client(self):
        self._client = None

    # subscription
    @property
    def subscription(self) -> Subscription:
        """Subscription to be pulled.

        If this is a string, it will be used along with `self.client` to create a
        `Subscription` object with the default `topic`, which will then replace it.
        If you need the subscription to be created and attached
        to a non-default `topic`, use a `Subscription` directly.

        If deleted, this is reset to None and the default subscription name is used with
        `self.client` to create the `Subscription` object.
        """
        if isinstance(self._subscription, str):
            self._subscription = Subscription(
                name=self._subscription, client=self.client
            )

        elif self._subscription is None:
            self._subscription = Subscription(client=self.client)

        return self._subscription

    @subscription.setter
    def subscription(self, value):
        self._subscription = value

    @subscription.deleter
    def subscription(self):
        self._subscription = None

    # stream
    @property
    def _queue(self) -> queue.Queue:
        """Queue to communicate between threads and enforce stopping conditions."""
        if self.__queue is None:
            self.__queue = queue.Queue()
        return self.__queue

    def stream(self) -> Optional[List]:
        """Execute a streaming pull and process messages through the callback(s).

        Messages are processed in a background thread through `self.callback`, which
        calls the user_callback if one is provided in the callback_kwargs.
        """
        # multi-threading
        # Google API has a thread scheduler that can run multiple background threads
        # and includes a queue, but I (Troy) haven't gotten it working yet.
        # self.scheduler = ThreadScheduler(ThreadPoolExecutor(max_workers))
        # self.scheduler.schedule(self.callback)

        # open a streaming-pull connection to the subscription
        # and process incoming messages through the callback, in a background thread
        LOGGER.info(f"Starting the streaming pull with configs {self.callback_kwargs}")
        self.streaming_pull_future = self.client.subscribe(
            self.subscription.path,
            self.callback,
            flow_control=pubsub_v1.types.FlowControl(
                max_messages=self.flow_configs.max_backlog
            ),
            # scheduler=self.scheduler,
            # await_callbacks_on_shutdown=True,
        )

        try:
            # Use the queue to count the processed messages and
            # stop when we hit a max_results or timeout stopping condition.
            total_count = 0
            while True:
                try:
                    total_count += self._queue.get(
                        block=True, timeout=self.flow_configs.timeout
                    )

                except queue.Empty:
                    LOGGER.info(
                        "Timeout stopping condition reached. Stopping the stream."
                    )
                    break

                else:
                    self._queue.task_done()

                    if (
                        self.flow_configs.max_results & total_count
                        >= self.flow_configs.max_results
                    ):
                        LOGGER.info(
                            "Max results stopping condition reached. "
                            "Stopping the stream."
                        )
                        break

            self._stop()

        # We must catch all errors so we can
        # stop the streaming pull and close the background thread before raising them.
        except (Keyboardinterrupt, Exception):
            self._stop()
            raise

        LOGGER.debug(
            (
                f"Processed {total_count} messages from {self.subscription_path}. "
                "The actual number of messages that were pulled and acknowledged "
                "may be higher if the user elected not to count some messages "
                "(e.g., by returning ``Response(result='filter_out')`` from the "
                "user_callback)."
            )
        )

        # if any results were collected, return them
        if len(self.results) > 0:
            return self.results

    def callback(self, message) -> None:
        """Process a single Pub/Sub message, run user_callback and handle response."""
        kwargs = self.callback_kwargs

        # Unpack the message, saving what's been requested
        try:
            alert = self._unpack_msg(message)  # Alert

        # catch any remaining error. log, nack, and return.
        except Exception as e:
            LOGGER.debug(
                (
                    "Error unpacking message; it will not be processed or acknowledged."
                    f"\nError: {e}\nMessage: {message}"
                )
            )
            message.nack()  # nack so message does not leave subscription
            return

        # Run the user_callback
        if kwargs.user_callback is not None:
            response = self.execute_user_callback(alert)

        # No user_callback was supplied. respond with success but log a warning
        else:
            LOGGER.warning(
                (
                    "No user_callback was supplied. Message will acknowledged but not "
                    "stored, and thus it will be lost. "
                    "If you simply want to store alerts for latter access, use "
                    "``consumer.callback_kwargs.user_callback = Consumer.collect_alert``."
                )
            )
            response = Response(ack=True, result=None)

        # take action on the response. ack and store as requested.
        count = self.handle_response(response, message)

        # Communicate with the main thread
        self._queue.put(count)
        if self.flow_configs.max_results is not None:
            # block until main thread acknowledges so we don't ack msgs that get lost
            self._queue.join()  # single background thread => one-in-one-out

    def _unpack_msg(self, message) -> Alert:
        """Return `Alert` object with data requested in self.callback_kwargs.include."""

        @staticmethod
        def _my_bytes(message):
            """Return alert data in original bytes format."""
            return message.data

        @staticmethod
        def _my_dict(message):
            """Return alert data as a dict."""
            return avro_to_dict(message.data)

        @staticmethod
        def _my_metadata(message):
            """Return message metadata and custom attributes as a dict."""
            return {
                "message_id": message.message_id,
                "publish_time": str(message.publish_time),
                **dict((k, v) for k, v in message.attributes.items()),
            }

        @staticmethod
        def _my_msg(message):
            """Return original Pub/Sub message object."""
            return message

        # map Alert attributes to functions that return the appropriate data
        extraction_map = dict(
            bytes=_my_bytes,
            dict=_my_dict,
            metadata=_my_metadata,
            msg=_my_msg,
        )

        # return an Alert, saving only what's requested in self.callback_kwargs.include
        return Alert(
            (k, _my_data(message))
            for k, _my_data in extraction_map.items
            if k in self.callback_kwargs.include
        )

    def execute_user_callback(self, alert) -> Response:
        """Try to executy user_callback, return an appropriate `Reponse`."""
        kwargs = self.callback_kwargs

        try:
            response = kwargs.user_callback(alert, **kwargs)  # Response

        # catch any remaining error, log it, and nack the msg
        except Exception as e:
            LOGGER.debug(
                "Error running user_callback. Message will not be acknowledged. "
                f"\nAlert: {alert}\nError:{e}"
            )
            response = Response(ack=False, result=None)

        else:
            # if user requested to nack, log it
            if not response.ack:
                LOGGER.debug(
                    (
                        "user_callback requested to NOT acknowledge the message."
                        f"\nAlert: {alert}"
                    )
                )

        return response

    @staticmethod
    def collect_alert(alert) -> Response:
        """Return a request to store the alert and acknowledge the message.

        To have alerts stored in `consumer.results` for later access, use this
        function as a user_callback, as in:
        `consumer.callback_kwargs.user_callback = Consumer.collect_alert`.
        """
        return Response(ack=True, result=alert)

    def handle_response(self, response, message) -> int:
        """Store a result if requested, then ack or nack the message."""
        # count message against max_results and store result, as appropriate
        try:
            # check for False
            if isinstance(response.result, bool) and not response.result:

                # don't count, don't store
                count = 0

            elif response.result is None:
                # count, don't store
                count = 1

            else:
                # count, store
                count = 1
                self.results.append(response.result)

        # if anything went wrong, warn and update the response so the message is nack'd
        except Exception as e:
            response = response._replace(ack=False)
            LOGGER.warning(
                f"Error handling the callback's response. Msg will be nack'd. {e}"
            )

        # ack or nack the message
        if response.ack:
            message.ack()
        else:
            message.nack()

        return count

    def _stop(self) -> None:
        """Shutdown the streaming pull in the background thread gracefully."""
        self.streaming_pull_future.cancel()  # Trigger the shutdown.
        self.streaming_pull_future.result()  # Block until the shutdown is complete.
