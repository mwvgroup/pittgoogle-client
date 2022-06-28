#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""Classes to facilitate connections to Pub/Sub streams.

.. contents:: Table of Contents
   :local:
   :depth: 2

.. note::

    This module relies on :mod:`pittgoogle.auth` to authenticate API calls.
    The examples given below use the :ref:`service account <service account>` option and
    assume that your :ref:`environment variables <set env vars>` are set.

Usage
------

In general, use a :class:`pittgoogle.pubsub.Consumer` to connect to a subscription and
pull messages.
The most basic instantiation looks like this:

.. code-block:: python

    from pittgoogle import pubsub

    consumer = pubsub.Consumer(pubsub.ConsumerSettings())

To learn about all of the available settings for the consumer,
see :class:`ConsumerSettings` and follow the type definition for each of its attributes.

Given a default :class:`ConsumerSettings()`, the consumer will try to create a
:class:`SubscriberClient()` using authentication information stored in environment
variables, and then connect to a Pub/Sub subscription defined by a default
:class:`Subscription()` (creating it, if necessary).

Each element of :class:`ConsumerSettings` becomes an attribute on the consumer.
So if, for example, you ran the code above and it created a subscription that you now
want to delete, you can do so using:

.. code-block:: python

    consumer.subscription.delete()

Pull and process messages
~~~~~~~~~~~~~~~~~~~~~~~~~~~

To pull messages from a subscription, use the :meth:`~Consumer.stream()` method.
This executes a "streaming pull" in a **background thread**.

To process and/or save alerts, you must use a :ref:`callback <callbacks>`.
The consumer will run each alert through your callback, in the background thread.
Here is the most basic example, which uses the example function
:meth:`Consumer.collect_alert` as the user callback.

.. code-block:: python

    from pittgoogle import pubsub

    settings = pubsub.ConsumerSettings(
        callback_settings=pubsub.CallbackSettings(
            user_callback=pubsub.Consumer.collect_alert
        )
    )
    consumer = pubsub.Consumer(settings)

    results = consumer.stream()

See :ref:`user callback` for more information.

.. _callbacks:

Callbacks Explainer
-------------------

(You may wish to jump directly to :ref:`user callback`.)

In Pub/Sub, a streaming pull happens in a background thread.
Thus, message processing should be handled by a callback function
(which is passed into the background thread by the client when it opens the
stream).
The callback should process a single message, persist the needed results, and then
:ref:`ack or nack <ack and nack>` the message.

By contrast, pulling an Apache Kafka stream typically results in Kafka returning
a batch of messages.
The user then processes messages by iterating through the batch.
Everything happens in the foreground thread.
You can mimic this behavior by using :meth:`Consumer.collect_alert` as your
user callback (explained below; especially note the warning).

The :class:`Consumer` uses two callbacks:
its :ref:`own callback() method <consumer callback>`
and a :ref:`user callback <user callback>`.
These are explained below.

.. _consumer callback:

Consumer callback
~~~~~~~~~~~~~~~~~~~~~~

The consumer's :meth:`~Consumer.callback()` method is called automatically
on each incoming message.
This method will:

#.  Unpack the Pub/Sub message into an :class:`pittgoogle.types.Alert()`, populating only the attributes
    reqested in :attr:`CallbackSettings.unpack`.

#.  Send the :class:`~pittgoogle.types.Alert()` through the user callback (explained below).

#.  Handle the :class:`~pittgoogle.types.Response()` returned by the user callback.
    This may include storing data in the consumer's :attr:`Consumer().results` attribute
    and :ref:`ack'ing or nack'ing <ack and nack>` the message.

#.  Communicate with the foreground thread.

.. _user callback:

User callback
~~~~~~~~~~~~~~~~~

A :attr:`~CallbackSettings.user_callback` is a function supplied by the user that
accepts a single :class:`pittgoogle.types.Alert`, processes the alert, and returns a :class:`pittgoogle.types.Response`.

Here is a template:

.. code-block:: python

    def my_user_callback(alert):
        # alert is an instance of pittgoogle.types.Alert
        alert_dict = alert.dict

        try:
            # process the alert_dict here
            # you should also save any results that you want to persist
            pass

        except:
            ack = False

        else:
            ack = True

        return Response(ack=ack, result=None)

And here is how to use it:

.. code-block:: python

    from pittgoogle import pubsub

    settings = pubsub.ConsumerSettings(
        callback_settings=pubsub.CallbackSettings(user_callback=my_user_callback)
    )
    consumer = pubsub.Consumer(settings)

    consumer.stream()

The incoming :class:`~pittgoogle.types.Alert` will contain data as requested via the
:attr:`~CallbackSettings.unpack` attribute.

The user callback can include arbitrary processing logic but it must be self-contained,
i.e., **it cannot rely on the state of the foreground thread**.
This callback is allowed to accept arbitrary keyword arguments, but their
values must be passed to the consumer via the :attr:`~CallbackSettings.user_kwargs`
setting prior to starting the pull.

After processing the alert, the user callback should return a :class:`~pittgoogle.types.Response`.
It is recommended that the callback persists its results on its own (e.g., by
sending to a database or writing to a file) rather than sending them back to the
consumer in the :attr:`~pittgoogle.types.Response.result` attribute.

.. warning::

    If you choose to send results back to the consumer through the
    :attr:`~pittgoogle.types.Response.result` attribute (as is done in :meth:`Consumer.collect_alert`),
    the results will not be available until the background thread has been closed.
    This increases the potential that collected results will fill up your memory,
    and also means that the results may be lost if a thread crashes.
    This option can be useful for testing, but it should not be combined with a
    large value of :attr:`FlowConfigs.max_results`.

.. _ack and nack:

ack and nack
~~~~~~~~~~~~~~

A :class:`pittgoogle.types.Response()` (to be returned by a :ref:`user callback`) contains
the boolean attribute :attr:`~Response.ack`, which indicates whether the message
should be ack'd (``ack=True``) or nack'd (``ack=False``).

**ack** is short for acknowledge.
ack should be used when the message has been processed successfully -- or at least to
an acceptable level such that the client/user does not need to see the message again.
Once Pub/Sub receives the ack, the message will be dropped from the subscription[*].

**nack** is the opposite of ack.
A nack'd message will remain in the subscription, and Pub/Sub will redeliver it to a
client at some arbitrary time in the future.
(Redelivery is usually immediate, though can be affected by, for example, the number of
messages in the subscription.)

In Pub/Sub, the subscriber client should either ack or nack each message it receives.
The consumer's :class:`~Consumer.handle_response()` method does this automatically,
based on the :class:`~pittgoogle.types.Response()` returned by the :ref:`user callback`.

This is a similar concept to setting the offset in an Apache Kafka topic/subscription.
However, a major difference is that Pub/Sub messages are not ordered[*], so one cannot
"fast-forward" or "rewind" the stream in the same way.
Instead, every Pub/Sub message is delivered, processed, and ack'd or nack'd
independently.

[*] Unless the subscription has been explicitly configured to behave otherwise.

Classes
--------

`ConsumerSettings`
~~~~~~~~~~~~~~~~~~~

.. autoclass:: pittgoogle.pubsub.ConsumerSettings
   :members:
   :member-order: bysource

`Consumer`
~~~~~~~~~~~~~~~~~~~

.. autoclass:: pittgoogle.pubsub.Consumer
   :members:
   :member-order: bysource

`Topic`
~~~~~~~~~~~~~~~~~~~

.. autoclass:: pittgoogle.pubsub.Topic
   :members:
   :member-order: bysource

`Subscription`
~~~~~~~~~~~~~~~~~~~

.. autoclass:: pittgoogle.pubsub.Subscription
   :members:
   :member-order: bysource

`SubscriberClient`
~~~~~~~~~~~~~~~~~~~

.. autoclass:: pittgoogle.pubsub.SubscriberClient
   :members:
   :member-order: bysource

`FlowConfigs`
~~~~~~~~~~~~~~~~~~~

.. autoclass:: pittgoogle.pubsub.FlowConfigs
   :members:
   :member-order: bysource

`CallbackSettings`
~~~~~~~~~~~~~~~~~~~

.. autoclass:: pittgoogle.pubsub.CallbackSettings
   :members:
   :member-order: bysource
"""
from dataclasses import dataclass
import logging
import os
from typing import Callable, Dict, List, Tuple, Optional, Union

# from concurrent.futures.thread import ThreadPoolExecutor
from google.api_core.exceptions import NotFound
from google.cloud import pubsub_v1

# from google.cloud.pubsub_v1.subscriber.scheduler import ThreadScheduler
import queue

from .auth import Auth, AuthSettings
from .types import Alert, Response, PittGoogleProjectIds
from .utils import avro_to_dict, class_defaults


LOGGER = logging.getLogger(__name__)


@dataclass
class Topic:
    """Basic attributes of a Pub/Sub topic.

    Attributes:
        name:
            Name of the Pub/Sub topic.
        projectid:
            The topic owner's Google Cloud project ID.
            Note that Pitt-Google's IDs can be
            obtained from :attr:`pittgoogle.types.PittGoogleProjectIds.production`,
            :attr:`pittgoogle.types.PittGoogleProjectIds.testing`, etc.
    """

    name: str = "ztf-loop"
    projectid: str = PittGoogleProjectIds.production

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
        """Class wrapper for :class:`pittgoogle.auth.Auth` object.

        If this is set to a :class:`pittgoogle.auth.AuthSettings` instance it will be
        used to instantiate a :class:`~pittgoogle.auth.Auth`, which will then replace it.

        The API call triggering authentication with Google Cloud is not made until
        either the :attr:`~pittgoogle.auth.Auth().credentials` or
        :attr:`~pittgoogle.auth.Auth().session` attribute is explicitly requested.

        Settings this manually will trigger reinstantiation of `self.client`.
        """
        if self._auth is None:
            # just warn and return
            LOGGER.warning(
                (
                    "No pittgoogle.auth.AuthSettings or pittgoogle.auth.Auth supplied. "
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
        """Class wrapper for a ``pubsub_v1.SubscriberClient`` object.

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
        """Class wrapper for a :class:`SubscriberClient()`.

        If this is set to a :class:`pittgoogle.auth.Auth` or
        :class:`pittgoogle.auth.AuthSettings` it will be used to instantiate a
        :class:`SubscriberClient`, which will then replace it.

        This will be required in order to connect to the subscription,
        but the connection is not checked during instantiation.
        """
        if self._client is None:
            # try to create a client using default AuthSettings
            LOGGER.debug(
                (
                    "No client or auth information provided. "
                    "Attempting to create a client using a default "
                    "pittgoogle.auth.AuthSettings()."
                )
            )
            self._client = SubscriberClient(AuthSettings())
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
        """Class wrapper for a :class:`Topic` that the subscription is or will be attached to.

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
            LOGGER.debug(
                f"A subscription named {self.name} does not exist in the "
                f"project {self.projectid}"
            )
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
class CallbackSettings:
    """Settings for a :meth:`Consumer.callback`.

    Attributes:
        user_callback:
            A function, supplied by the user, that accepts a single :class:`pittgoogle.types.Alert` as
            its sole argument and returns a :class:`pittgoogle.types.Response`.
            The function is allowed to accept arbitrary keyword arguments, but their
            values must be passed to the consumer via the `user_kwargs` setting prior
            to starting the pull.
            See :ref:`user callback` for more information.
        user_kwargs:
            A dictionary of key/value pairs that will be sent as kwargs to the
            `user_callback` by the consumer.
        unpack:
            This determines which data is extracted from the Pub/Sub message into an
            :class:`~pittgoogle.types.Alert`, and thus made available to the user callback.
            This should be a tuple of :class:`~pittgoogle.types.Alert` attributes (the attribute name as
            a string) to be populated.
    """

    user_callback: Optional[Callable[[Alert], Response]] = None
    user_kwargs: Optional[Dict] = None
    unpack: Tuple[str] = tuple(["dict"])


@dataclass
class FlowConfigs:
    """Stopping conditions and flow control settings for a :class:`Consumer`."""

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
                    "This can result in an excessive number of pulled messages that "
                    "will never be processed. "
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
class ConsumerSettings:
    """Settings for a :class:`Consumer`.

    Attributes:
        client:
            Either a :class:`SubscriberClient` or the :class:`pittgoogle.auth.Auth`
            or :class:`pittgoogle.auth.AuthSettings` necessary to create one.

        subscription:
            Pub/Sub subscription to be pulled.

        flow_configs:
            Stopping conditions and flow control settings for the streaming pull.

        callback_settings:
            Settings for the :ref:`callbacks <callbacks>`.
            These dictate the message delivery format, processing logic, and data
            returned.
    """

    client: Union[SubscriberClient, Auth, AuthSettings] = AuthSettings()
    subscription: Union[str, Subscription] = "ztf-loop"
    flow_configs: FlowConfigs = FlowConfigs()
    callback_settings: CallbackSettings = CallbackSettings()


@dataclass
class Consumer:
    """Consumer class to pull a Pub/Sub subscription and process messages.

    Args:
        settings:
            An instance of :class:`ConsumerSettings()`.

    Initialization does the following:

    #.  Unpack each element of `settings` into a property of `self`.

    #.  Authenticate the client by requesting credentials
        (``self.client.auth.credentials``).

    #.  Make sure the subscription exists in Pub/Sub (creating it, if necessary), and
        that the client can connect (``self.subscription.touch()``).
    """

    def __init__(self, settings: ConsumerSettings):
        LOGGER.debug(
            f"Instantiating consumer with the following settings: {settings.__repr__()}"
        )

        # unpack consumer settings to attributes
        self._client = settings.client
        self._subscription = settings.subscription
        self.flow_configs = settings.flow_configs
        self.callback_settings = settings.callback_settings

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
        """Class wrapper for a :class:`SubscriberClient`.

        If this is set to a :class:`pittgoogle.auth.Auth` or :class:`pittgoogle.auth.AuthSettings` it will be used to
        instantiate a :class:`SubscriberClient`, which will then replace it.
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

        If this is set to a string it will be used along with `self.client` to create a
        :class:`Subscription` with the default topic, which will then replace it.
        If you need the subscription to be created and attached
        to a non-default topic, use a :class:`Subscription` directly.

        If deleted, this is reset to None and the default subscription name is used with
        `self.client` to create the :class:`Subscription`.
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

    def stream(self, block: bool = True) -> Optional[List]:
        """Execute a streaming pull and process messages through the :ref:`callbacks <callbacks>`.

        This method starts a streaming pull in a background thread.
        Subsequent behavior is determined by the `block` kwarg.

        Args:
            block:
                Whether to block the foreground thread during the pull.

                If True (default), the consumer manages the flow of messages and
                enforces the stopping conditions set in the
                :attr:`~ConsumerSettings.flow_configs` attribute.

                If false, this method returns None immediately after opening the stream.
                Use this option with caution.
                The pull will continue in the background, but the consumer will not
                automatically control the flow (e.g., it will not enforce the stopping
                conditions).
                Thus the pull can run in the background indefinitely.
                You can stop it manually by calling the consumer's
                :meth:`~Consumer.stop()` method.
                If you want this option, consider opening the stream by calling the
                Pub/Sub API directly.
                This will give you more control over the pull (including the option
                to parallelize it).
                The command is documented
                `here <https://googleapis.dev/python/pubsub/latest/subscriber/api/client.html#google.cloud.pubsub_v1.subscriber.client.Client.subscribe>`__.
                It can be executed using the consumer's client:

                .. code-block:: python

                    from pittgoogle import pubsub

                    consumer = pubsub.Consumer(pubsub.ConsumerSettings())
                    consumer.streaming_pull_future = consumer.client.client.subscribe()

                (also send appropriate args/kwargs).
                Assigning the result to the consumer's streaming_pull_future attribute
                will allow you to use ``consumer.stop()``.

        Return:
            List of results, if any, that the user callback passed back to the consumer
            via :attr:`~pittgoogle.types.Response.result`.
        """
        # tell the callback whether the consumer is actively managing the queue
        self.callback_settings.block = block

        # multi-threading
        # Google API has a thread scheduler that can run multiple background threads
        # and includes a queue, but I (Troy) haven't gotten it working yet.
        # self.scheduler = ThreadScheduler(ThreadPoolExecutor(max_workers))
        # self.scheduler.schedule(self.callback)

        # open a streaming-pull connection to the subscription
        # and process incoming messages through the callback, in a background thread
        LOGGER.info(
            (
                f"Starting a streaming pull on the subscription: {self.subscription}"
                f"using flow_configs: {self.flow_configs} "
                f"and callback_settings: {self.callback_settings}"
            )
        )
        self.streaming_pull_future = self.client.subscribe(
            self.subscription.path,
            self.callback,
            flow_control=pubsub_v1.types.FlowControl(
                max_messages=self.flow_configs.max_backlog
            ),
            # scheduler=self.scheduler,
            # await_callbacks_on_shutdown=True,
        )

        if not block:
            return

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

            self.stop()

        # We must catch all errors so we can
        # stop the streaming pull and close the background thread before raising them.
        except (Keyboardinterrupt, Exception):
            self.stop()
            raise

        LOGGER.debug(
            (
                f"Processed {total_count} messages from {self.subscription.path}. "
                "The actual number of messages that were pulled and acknowledged "
                "may be higher if the user elected not to count some messages "
                "(e.g., by returning ``Response(result='filter_out')`` from the "
                "user_callback)."
            )
        )

        # if any results were collected, return them
        if len(self.results) > 0:
            return self.results

    def callback(self, message: pubsub_v1.types.PubsubMessage) -> None:
        """Unpack the message, run the :attr:`~CallbackSettings.user_callback` and handle the response."""
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
        if self.callback_settings.user_callback is not None:
            response = self.execute_user_callback(alert)

        # No user_callback was supplied. respond with success but log a warning
        else:
            LOGGER.warning(
                (
                    "No user_callback was supplied. The message will be acknowledged "
                    "but not stored, and thus it will be lost. "
                    "If you're not sure what to do, try using the "
                    "Consumer.collect_alert method (http://pittgoogle-client.rtfd.io)."
                )
            )
            response = Response(ack=True, result=None)

        # take action on the response. ack and store as requested.
        self.handle_response(response, message)

    def _unpack_msg(self, message: pubsub_v1.types.PubsubMessage) -> Alert:
        """Return an :class:`~pittgoogle.types.Alert` with data requested in :attr:`~CallbackSettings.unpack."""

        @staticmethod
        def _my_bytes(message):
            """Return the message payload without changing the format."""
            return message.data

        @staticmethod
        def _my_dict(message):
            """Return the message payload as a dictionary."""
            return avro_to_dict(message.data)

        @staticmethod
        def _my_metadata(message):
            """Return the message metadata and custom attributes as a dictionary."""
            return {
                "message_id": message.message_id,
                "publish_time": message.publish_time,
                # ordering must be enabled on the subscription for this to be useful
                "ordering_key": message.ordering_key,
                **dict((k, v) for k, v in message.attributes.items()),
            }

        @staticmethod
        def _my_msg(message):
            """Return the original Pub/Sub message object."""
            return message

        # map Alert attributes to functions that return the appropriate data
        unpack_map = dict(
            bytes=_my_bytes,
            dict=_my_dict,
            metadata=_my_metadata,
            msg=_my_msg,
        )

        # return an Alert, saving only what's requested in callback_settings.unpack
        return Alert(
            (k, _my_data(message))
            for k, _my_data in unpack_map.items
            if k in self.callback_settings.unpack
        )

    def execute_user_callback(self, alert: Alert) -> Response:
        """Try to execute the :attr:`~CallbackSettings.user_callback`, return an appropriate Response."""
        kwargs = self.callback_settings.user_kwargs
        if kwargs is None:
            kwargs = dict()

        try:
            response = self.callback_settings.user_callback(alert, **kwargs)  # Response

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
    def collect_alert(alert: Alert) -> Response:
        """:ref:`user callback` example that simply requests that the alert be collected.

        Returns:
            ``Response(ack=True, result=alert)``

        Use this as the :attr:`~CallbackSettings.user_callback` if you want the alerts
        stored in the consumer's :attr:`~Consumer.results` attribute for later access.

        consumer.callback_settings.user_callback = Consumer.collect_alert
        """
        return Response(ack=True, result=alert)

    def handle_response(
        self, response: Response, message: pubsub_v1.types.PubsubMessage
    ) -> int:
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

        # Communicate with the main thread
        if self.callback_settings.block:
            self._queue.put(count)
            if self.flow_configs.max_results is not None:
                # block until main thread acknowledges so we don't ack msgs that get lost
                self._queue.join()  # single background thread => one-in-one-out

        # ack or nack the message
        if response.ack:
            message.ack()
        else:
            message.nack()

        return count

    def stop(self) -> None:
        """Shutdown the streaming pull and exit the background thread gracefully."""
        self.streaming_pull_future.cancel()  # Trigger the shutdown.
        self.streaming_pull_future.result()  # Block until the shutdown is complete.
