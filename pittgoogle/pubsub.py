# -*- coding: UTF-8 -*-
"""Classes to facilitate connections to Google Cloud Pub/Sub streams.

.. autosummary::

    Consumer
    Response
    Subscription
    Topic

----
"""
import concurrent.futures
import datetime
import logging
import queue
import time
from typing import Any, Callable, List, Literal, Optional, Union

import attrs
import attrs.validators
import google.api_core.exceptions
import google.cloud.pubsub_v1

from . import exceptions
from .alert import Alert
from .auth import Auth

LOGGER = logging.getLogger(__name__)


def msg_callback_example(alert: Alert) -> "Response":
    print(f"processing message: {alert.metadata['message_id']}")
    return Response(ack=True, result=alert.dict)


def batch_callback_example(batch: list) -> None:
    oids = set(alert.dict["objectId"] for alert in batch)
    print(f"num oids: {len(oids)}")
    print(f"batch length: {len(batch)}")


def pull_batch(
    subscription: Union[str, "Subscription"],
    max_messages: int = 1,
    schema_name: str = str(),
    **subscription_kwargs,
) -> List["Alert"]:
    """Pulls a single batch of messages from the specified subscription.

    Args:
        subscription (str or Subscription):
            The subscription to be pulled. If str, the name of the subscription. The subscription is
            expected to exist in Google Cloud.
        max_messages (int):
            The maximum number of messages to be pulled.
        schema_name (str):
            The schema name of the alerts in the subscription. See :meth:`pittgoogle.registry.Schemas.names`
            for the list of options. Passed to Alert for unpacking. If not provided, some properties of
            the Alert may not be available.
        **subscription_kwargs:
            Keyword arguments used to create the :class:`Subscription` object, if needed.

    Returns:
        list[Alert]:
            A list of Alert objects representing the pulled messages.
    """
    if isinstance(subscription, str):
        subscription = Subscription(subscription, **subscription_kwargs)

    try:
        response = subscription.client.pull(
            {"subscription": subscription.path, "max_messages": max_messages}
        )
    except google.api_core.exceptions.NotFound as excep:
        msg = f"NotFound: {subscription.path}. You may need to create the subscription using `pittgoogle.Subscription.touch`."
        raise exceptions.CloudConnectionError(msg) from excep

    alerts = [
        Alert.from_msg(msg.message, schema_name=schema_name) for msg in response.received_messages
    ]

    ack_ids = [msg.ack_id for msg in response.received_messages]
    if len(ack_ids) > 0:
        subscription.client.acknowledge({"subscription": subscription.path, "ack_ids": ack_ids})

    return alerts


@attrs.define
class Topic:
    """Class to manage a Google Cloud Pub/Sub topic.

    Args:
        name (str):
            Name of the Pub/Sub topic.
        projectid (str, optional):
            The topic owner's Google Cloud project ID. Either this or ``auth`` is required. Use this
            if you are connecting to a subscription owned by a different project than this topic.
            :class:`pittgoogle.registry.ProjectIds` is a registry containing Pitt-Google's project IDs.
        auth (Auth, optional):
            Credentials for the Google Cloud project that owns this topic. If not provided,
            it will be created from environment variables when needed.
        client (google.cloud.pubsub_v1.PublisherClient, optional):
            Pub/Sub client that will be used to access the topic. If not provided,
            a new client will be created the first time it is requested.

    Example:

        .. code-block:: python

            # Create a new topic in your project
            my_topic = pittgoogle.Topic(name="my-new-topic")
            my_topic.touch()

            # Create a dummy message to publish
            my_alert = pittgoogle.Alert(
                dict={"message": "Hello, World!"},  # the message payload
                attributes={"custom_key": "custom_value"}  # custom attributes for the message
            )

            # Publish the message to the topic
            my_topic.publish(my_alert)  # returns the ID of the published message

        To pull the message back from the topic, use a :class:`Subscription`.

    ----
    """

    name: str = attrs.field()
    _projectid: str = attrs.field(default=None)
    _auth: Auth = attrs.field(
        default=None, validator=attrs.validators.optional(attrs.validators.instance_of(Auth))
    )
    _client: Optional[google.cloud.pubsub_v1.PublisherClient] = attrs.field(
        default=None,
        validator=attrs.validators.optional(
            attrs.validators.instance_of(google.cloud.pubsub_v1.PublisherClient)
        ),
    )

    @classmethod
    def from_cloud(
        cls,
        name: str,
        *,
        projectid: str,
        survey: Optional[str] = None,
        testid: Optional[str] = None,
    ):
        """Creates a :class:`Topic` with a :attr:`Topic.client` that uses implicit credentials.

        Args:
            name (str):
                Name of the topic. If ``survey`` and/or ``testid`` are provided, they will be added to this
                name following the Pitt-Google naming syntax.
            projectid (str):
                Project ID of the Google Cloud project that owns this resource. Project IDs used by
                Pitt-Google are listed in the registry for convenience (:class:`pittgoogle.registry.ProjectIds`).
                Required because it cannot be retrieved from the `client` and there is no explicit `auth`.
            survey (str, optional):
                Name of the survey. If provided, it will be prepended to `name` following the
                Pitt-Google naming syntax.
            testid (str, optional):
                Pipeline identifier. If this is not None, False, or "False", it will be appended to
                the ``name`` following the Pitt-Google naming syntax. This is used to allow pipeline modules
                to find the correct resources without interfering with other pipelines that may have
                deployed resources with the same base names (e.g., for development and testing purposes).
        """
        # if survey and/or testid passed in, use them to construct full name using the pitt-google naming syntax
        if survey is not None:
            name = f"{survey}-{name}"
        # must accommodate False and "False" for consistency with the broker pipeline
        if testid and testid != "False":
            name = f"{name}-{testid}"
        return cls(name, projectid=projectid, client=google.cloud.pubsub_v1.PublisherClient())

    @classmethod
    def from_path(cls, path) -> "Topic":
        """Parse the ``path`` and return a new :class:`Topic`."""
        _, projectid, _, name = path.split("/")
        return cls(name, projectid)

    @property
    def auth(self) -> Auth:
        """Credentials for the Google Cloud project that owns this topic.

        This will be created from environment variables if needed.
        """
        if self._auth is None:
            self._auth = Auth()
        return self._auth

    @property
    def path(self) -> str:
        """Fully qualified path to the topic."""
        return f"projects/{self.projectid}/topics/{self.name}"

    @property
    def projectid(self) -> str:
        """The topic owner's Google Cloud project ID."""
        if self._projectid is None:
            self._projectid = self.auth.GOOGLE_CLOUD_PROJECT
        return self._projectid

    @property
    def client(self) -> google.cloud.pubsub_v1.PublisherClient:
        """Pub/Sub client for topic access.

        Will be created using :attr:`Topic.auth.credentials` if necessary.
        """
        if self._client is None:
            self._client = google.cloud.pubsub_v1.PublisherClient(
                credentials=self.auth.credentials
            )
        return self._client

    def touch(self) -> None:
        """Test the connection to the topic, creating it if necessary.

        .. tip: This is only necessary if you need to interact with the topic directly to do things like
            *publish* messages. In particular, this is *not* necessary if you are trying to *pull* messages.
            All users can create a subscription to a Pitt-Google topic and pull messages from it, even
            if they can't actually touch the topic.

        Raises:
            CloudConnectionError:
                'PermissionDenied' if :attr:`Topic.auth` does not have permission to get or create the table.
        """
        try:
            # Check if topic exists and we can connect.
            self.client.get_topic(topic=self.path)
            LOGGER.info(f"topic exists: {self.path}")

        except google.api_core.exceptions.NotFound:
            try:
                # Try to create a new topic.
                self.client.create_topic(name=self.path)
                LOGGER.info(f"topic created: {self.path}")

            except google.api_core.exceptions.PermissionDenied as excep:
                # User has access to this topic's project but insufficient permissions to create a new topic.
                # Assume this is a simple IAM problem rather than the user being confused about when
                # to call this method (as can happen below).
                msg = (
                    "PermissionDenied: You seem to have appropriate IAM permissions to get topics "
                    "in this project but not to create them."
                )
                raise exceptions.CloudConnectionError(msg) from excep

        except google.api_core.exceptions.PermissionDenied as excep:
            # User does not have permission to get this topic.
            # This is not a problem if they only want to subscribe, but can be confusing.
            # [TODO] Maybe users should just be allowed to get the topic?
            msg = (
                f"PermissionDenied: The provided `pittgoogle.Auth` cannot get topic {self.path}. "
                "Either the provided Auth has a different project ID, or your credentials just don't "
                "have appropriate IAM permissions. \nNote that if you are a user trying to connect to "
                "a Pitt-Google topic, your Auth is _expected_ to have a different project ID and you "
                "can safely ignore this error (and avoid running `Topic.touch` in the future). "
                "It does not impact your ability to attach a subscription and pull messages."
            )
            raise exceptions.CloudConnectionError(msg) from excep

    def delete(self) -> None:
        """Delete the topic."""
        try:
            self.client.delete_topic(topic=self.path)
        except google.api_core.exceptions.NotFound:
            LOGGER.info(f"nothing to delete. topic not found: {self.path}")
        else:
            LOGGER.info(f"deleted topic: {self.path}")

    def publish(
        self,
        alert: "Alert",
        serializer: Literal["json", "avro", None] = None,
        drop_cutouts: bool = False,
    ) -> int:
        """Publish a message with :attr:`pittgoogle.Alert.dict` as the payload and
        :attr:`pittgoogle.Alert.attributes` as the attributes.

        Args:
            alert (Alert):
                The alert to be published.
            serializer (str or None, optional):
                Whether to serialize the dict using Avro or JSON. If not None, this will override
                :meth:`pittgoogle.Alert.schema.serializer` and is subject to the same conditions.
            drop_cutouts (bool):
                Whether to drop cutouts from the alert dict before publishing. This is useful for
                reducing the size of the message when cutouts are not needed.

        Returns:
            int:
                Pub/Sub message ID of the published message.
        """
        _serializer = serializer or alert.schema.serializer
        alert_dict = alert.dict if not drop_cutouts else alert.drop_cutouts()
        message = alert.schema.serialize(alert_dict, serializer=_serializer)
        # Pub/Sub requires attribute keys and values to be strings. Sort by key while we're at it.
        attributes = {str(key): str(self.attributes[key]) for key in sorted(self.attributes)}
        future = self.client.publish(self.path, data=message, **attributes)
        return future.result()


@attrs.define
class Subscription:
    """Class to manage a Google Cloud Pub/Sub subscription.

    Args:
        name (str):
            Name of the Pub/Sub subscription.
        auth (Auth, optional):
            Credentials for the Google Cloud project that will be used to connect to the subscription.
            If not provided, it will be created from environment variables.
        topic (Topic, optional):
            Topic this subscription should be attached to. Required only when the subscription needs to be created.
        client (google.cloud.pubsub_v1.SubscriberClient, optional):
            Pub/Sub client that will be used to access the subscription.
            If not provided, a new client will be created the first time it is needed.
        schema_name (str):
            Schema name of the alerts in the subscription. Passed to :class:`pittgoogle.alert.Alert` for unpacking.
            If not provided, some properties of the Alert may not be available. For a list of schema names, see
            :meth:`pittgoogle.registry.Schemas.names`.

    Example:

        Create a subscription to Pitt-Google's 'ztf-loop' topic and pull messages:

        .. code-block:: python

            # Topic that the subscription should be connected to
            topic = pittgoogle.Topic(name="ztf-loop", projectid=pittgoogle.ProjectIds().pittgoogle)

            # Create the subscription
            subscription = pittgoogle.Subscription(
                name="my-ztf-loop-subscription", topic=topic, schema_name="ztf"
            )
            subscription.touch()

            # Pull a small batch of alerts
            alerts = subscription.pull_batch(max_messages=4)

    ----
    """

    name: str = attrs.field()
    auth: Auth = attrs.field(factory=Auth, validator=attrs.validators.instance_of(Auth))
    topic: Optional[Topic] = attrs.field(
        default=None, validator=attrs.validators.optional(attrs.validators.instance_of(Topic))
    )
    _client: Optional[google.cloud.pubsub_v1.SubscriberClient] = attrs.field(
        default=None,
        validator=attrs.validators.optional(
            attrs.validators.instance_of(google.cloud.pubsub_v1.SubscriberClient)
        ),
    )
    schema_name: str | None = attrs.field(default=None)

    @property
    def projectid(self) -> str:
        """Subscription owner's Google Cloud project ID."""
        return self.auth.GOOGLE_CLOUD_PROJECT

    @property
    def path(self) -> str:
        """Fully qualified path to the subscription."""
        return f"projects/{self.projectid}/subscriptions/{self.name}"

    @property
    def client(self) -> google.cloud.pubsub_v1.SubscriberClient:
        """Pub/Sub client that will be used to access the subscription.

        If not provided, a new client will be created using :attr:`Subscription.auth`.
        """
        if self._client is None:
            self._client = google.cloud.pubsub_v1.SubscriberClient(
                credentials=self.auth.credentials
            )
        return self._client

    def touch(self) -> None:
        """Test the connection to the subscription, creating it if necessary.

        Note that messages published to the topic before the subscription was created are
        not available to the subscription.

        Raises:
            TypeError:
                if the subscription needs to be created but no topic was provided.

            CloudConnectionError:

                - 'NotFound` if the subscription needs to be created but the topic does not exist in Google Cloud.
                - 'InvalidTopic' if the subscription exists but the user explicitly provided a topic that
                   this subscription is not actually attached to.
        """
        try:
            subscrip = self.client.get_subscription(subscription=self.path)
            LOGGER.info(f"subscription exists: {self.path}")

        except google.api_core.exceptions.NotFound:
            subscrip = self._create()  # may raise TypeError or CloudConnectionError
            LOGGER.info(f"subscription created: {self.path}")

        self._set_topic(subscrip.topic)  # may raise CloudConnectionError

    def _create(self) -> google.cloud.pubsub_v1.types.Subscription:
        if self.topic is None:
            raise TypeError("The subscription needs to be created but no topic was provided.")

        try:
            return self.client.create_subscription(name=self.path, topic=self.topic.path)

        # this error message is not very clear. let's help.
        except google.api_core.exceptions.NotFound as excep:
            msg = f"NotFound: The subscription cannot be created because the topic does not exist: {self.topic.path}"
            raise exceptions.CloudConnectionError(msg) from excep

    def _set_topic(self, connected_topic_path) -> None:
        # if the topic is invalid, raise an error
        if (self.topic is not None) and (connected_topic_path != self.topic.path):
            msg = (
                "InvalidTopic: The subscription exists but is attached to a different topic.\n"
                f"\tFound topic: {connected_topic_path}\n"
                f"\tExpected topic: {self.topic.path}\n"
                "Either use the found topic or delete the existing subscription and try again."
            )
            raise exceptions.CloudConnectionError(msg)

        # if the topic isn't already set, do it now
        if self.topic is None:
            self.topic = Topic.from_path(connected_topic_path)
        LOGGER.debug("topic validated")

    def delete(self) -> None:
        """Delete the subscription."""
        try:
            self.client.delete_subscription(subscription=self.path)
        except google.api_core.exceptions.NotFound:
            LOGGER.info(f"nothing to delete. subscription not found: {self.path}")
        else:
            LOGGER.info(f"deleted subscription: {self.path}")

    def pull_batch(self, max_messages: int = 1) -> List["Alert"]:
        """Pull a single batch of messages.

        This method is recommended for use cases that need a small number of alerts on-demand,
        often for testing and development.

        This method is *not* recommended for long-running listeners as it is likely to be unstable.
        Use :meth:`Consumer.stream` instead. This is Google's recommendation about how to use the
        Google API that underpins these pittgoogle methods.

        Args:
            max_messages (int):
                Maximum number of messages to be pulled.

        Returns:
            list[Alert]:
                A list of Alert objects representing the pulled messages.
        """
        # Wrapping the module-level function
        return pull_batch(self, max_messages=max_messages, schema_name=self.schema_name)

    def purge(self):
        """Purge all messages from the subscription."""
        msg = (
            "WARNING: This is permanent.\n"
            f"Are you sure you want to purge all messages from the subscription\n{self.path}?\n"
            "(y/[n]): "
        )
        proceed = input(msg)
        if proceed.lower() == "y":
            LOGGER.info(f"Purging all messages from subscription {self.path}")
            _ = self.client.seek(
                request=dict(subscription=self.path, time=datetime.datetime.now())
            )


@attrs.define
class Consumer:
    """Consumer class to pull a Pub/Sub subscription and process messages.

    Args:
        subscription (str or Subscription):
            Pub/Sub subscription to be pulled (it must already exist in Google Cloud).
        msg_callback (callable):
            Function that will process a single message. It should accept a Alert and return a Response.
        batch_callback (callable, optional):
            Function that will process a batch of results. It should accept a list of the results
            returned by the msg_callback.
        batch_maxn (int, optional):
            Maximum number of messages in a batch. This has no effect if batch_callback is None.
        batch_max_wait_between_messages (int, optional):
            Max number of seconds to wait between messages before processing a batch. This has
            no effect if batch_callback is None.
        max_backlog (int, optional):
            Maximum number of pulled but unprocessed messages before pausing the pull.
        max_workers (int, optional):
            Maximum number of workers for the executor. This has no effect if an executor is provided.
        executor (concurrent.futures.ThreadPoolExecutor, optional):
            Executor to be used by the Google API to pull and process messages in the background.

    Example:

        Open a streaming pull. Recommended for long-running listeners. This will pull and process
        messages in the background, indefinitely. User must supply a callback that processes a single message.
        It should accept a :class:`pittgoogle.pubsub.Alert` and return a :class:`pittgoogle.pubsub.Response`.
        Optionally, can provide a callback that processes a batch of messages. Note that messages are
        acknowledged (and thus permanently deleted) _before_ the batch callback runs, so it is recommended
        to do as much processing as possible in the message callback and use a batch callback only when
        necessary.

        .. code-block:: python

            def my_msg_callback(alert):
                # process the message here. we'll just print the ID.
                print(f"processing message: {alert.metadata['message_id']}")

                # return a Response. include a result if using a batch callback.
                return pittgoogle.pubsub.Response(ack=True, result=alert.dict)

            def my_batch_callback(results):
                # process the batch of results (list of results returned by my_msg_callback)
                # we'll just print the number of results in the batch
                print(f"batch processing {len(results)} results)

            consumer = pittgoogle.pubsub.Consumer(
                subscription=subscription, msg_callback=my_msg_callback, batch_callback=my_batch_callback
            )

            # open the stream in the background and process messages through the callbacks
            # this blocks indefinitely. use `Ctrl-C` to close the stream and unblock
            consumer.stream()

    ----
    """

    _subscription: Union[str, Subscription] = attrs.field(
        validator=attrs.validators.instance_of((str, Subscription))
    )
    msg_callback: Callable[["Alert"], "Response"] = attrs.field(
        validator=attrs.validators.is_callable()
    )
    batch_callback: Optional[Callable[[list], None]] = attrs.field(
        default=None, validator=attrs.validators.optional(attrs.validators.is_callable())
    )
    batch_maxn: int = attrs.field(default=100, converter=int)
    batch_max_wait_between_messages: int = attrs.field(default=30, converter=int)
    max_backlog: int = attrs.field(default=1000, validator=attrs.validators.gt(0))
    max_workers: Optional[int] = attrs.field(
        default=None, validator=attrs.validators.optional(attrs.validators.instance_of(int))
    )
    _executor: concurrent.futures.ThreadPoolExecutor = attrs.field(
        default=None,
        validator=attrs.validators.optional(
            attrs.validators.instance_of(concurrent.futures.ThreadPoolExecutor)
        ),
    )
    _queue: queue.Queue = attrs.field(factory=queue.Queue, init=False)
    streaming_pull_future: google.cloud.pubsub_v1.subscriber.futures.StreamingPullFuture = (
        attrs.field(default=None, init=False)
    )

    @property
    def subscription(self) -> Subscription:
        """Subscription to be consumed."""
        if isinstance(self._subscription, str):
            self._subscription = Subscription(self._subscription)
            self._subscription.touch()
        return self._subscription

    @property
    def executor(self) -> concurrent.futures.ThreadPoolExecutor:
        """Executor to be used by the Google API for a streaming pull."""
        if self._executor is None:
            self._executor = concurrent.futures.ThreadPoolExecutor(self.max_workers)
        return self._executor

    def stream(self, block: bool = True) -> None:
        """Open the stream in a background thread and process messages through the callbacks.

        Recommended for long-running listeners.

        Args:
            block (bool):
                Whether to block the main thread while the stream is open. If `True`, block
                indefinitely (use `Ctrl-C` to close the stream and unblock). If `False`, open the
                stream and then return (use :meth:`~Consumer.stop()` to close the stream).
                This must be `True` in order to use a `batch_callback`.
        """
        # open a streaming-pull and process messages through the callback, in the background
        self._open_stream()

        if not block:
            msg = "The stream is open in the background. Use consumer.stop() to close it."
            print(msg)
            LOGGER.info(msg)
            return

        try:
            self._process_batches()

        # catch all exceptions and attempt to close the stream before raising
        except (KeyboardInterrupt, Exception):
            self.stop()
            raise

    def _open_stream(self) -> None:
        """Open a streaming pull and process messages in the background."""
        LOGGER.info(f"opening a streaming pull on subscription: {self.subscription.path}")
        self.streaming_pull_future = self.subscription.client.subscribe(
            self.subscription.path,
            self._callback,
            flow_control=google.cloud.pubsub_v1.types.FlowControl(max_messages=self.max_backlog),
            scheduler=google.cloud.pubsub_v1.subscriber.scheduler.ThreadScheduler(
                executor=self.executor
            ),
            await_callbacks_on_shutdown=True,
        )

    def _callback(self, message: google.cloud.pubsub_v1.types.PubsubMessage) -> None:
        """Unpack the message, run the :attr:`~Consumer.msg_callback` and handle the response."""
        # LOGGER.info("callback started")
        response = self.msg_callback(Alert(msg=message))  # Response
        # LOGGER.info(f"{response.result}")

        if response.result is not None:
            self._queue.put(response.result)

        if response.ack:
            message.ack()
        else:
            message.nack()

    def _process_batches(self):
        """Run the batch callback if provided, otherwise just sleep.

        This never returns -- it runs until it encounters an error.
        """
        # if there's no batch_callback there's nothing to do except wait until the process is killed
        if self.batch_callback is None:
            while True:
                time.sleep(60)

        batch, count = [], 0
        while True:
            try:
                batch.append(
                    self._queue.get(block=True, timeout=self.batch_max_wait_between_messages)
                )

            except queue.Empty:
                # hit the max wait. process the batch
                self.batch_callback(batch)
                batch, count = [], 0

            # catch anything else and try to process the batch before raising
            except (KeyboardInterrupt, Exception):
                self.batch_callback(batch)
                raise

            else:
                self._queue.task_done()
                count += 1

            if count == self.batch_maxn:
                # hit the max number of results. process the batch
                self.batch_callback(batch)
                batch, count = [], 0

    def stop(self) -> None:
        """Attempt to shutdown the streaming pull and exit the background threads gracefully."""
        LOGGER.info("closing the stream")
        self.streaming_pull_future.cancel()  # trigger the shutdown
        self.streaming_pull_future.result()  # block until the shutdown is complete

    def pull_batch(self, max_messages: int = 1) -> List["Alert"]:
        """Pull a single batch of messages.

        Recommended for testing. Not recommended for long-running listeners (use the
        :meth:`~Consumer.stream` method instead).

        Args:
            max_messages (int):
                Maximum number of messages to be pulled.

        Returns:
            list[Alert]:
                A list of Alert objects representing the pulled messages.
        """
        return self.subscription.pull_batch(max_messages=max_messages)


@attrs.define(kw_only=True, frozen=True)
class Response:
    """Container for a response, to be returned by a :meth:`Consumer.msg_callback`.

    Args:
        ack (bool):
            Whether to acknowledge the message. Use `True` if the message was processed successfully,
            `False` if an error was encountered and you would like Pub/Sub to redeliver the message at
            a later time. Note that once a message is acknowledged to Pub/Sub it is permanently deleted
            (unless the subscription has been explicitly configured to retain acknowledged messages).

        result (Any):
            Anything the user wishes to return. If not `None`, the Consumer will collect the results
            in a list and pass the list to the user's batch callback for further processing.
            If there is no batch callback the results will be lost.

    ----
    """

    ack: bool = attrs.field(default=True, converter=bool)
    result: Any = attrs.field(default=None)
