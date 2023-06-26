# -*- coding: UTF-8 -*-
"""Classes to facilitate connections to Pub/Sub streams.

.. contents::
   :local:
   :depth: 2

.. note::

    This module relies on :mod:`pittgoogle.auth` to authenticate API calls.
    The examples given below assume the use of a :ref:`service account <service account>` and
    :ref:`environment variables <set env vars>`. In this case, :mod:`pittgoogle.auth` does not
    need to be called explicitly.

Usage Examples
---------------

.. code-block:: python

    import pittgoogle

Create a subscription to the "ztf-loop" topic:

.. code-block:: python

    subscription = pittgoogle.pubsub.Subscription(
        "my-ztf-loop-subscription",
        # topic only required if the subscription does not yet exist in Google Cloud
        topic=pittgoogle.pubsub.Topic("ztf-loop", pittgoogle.utils.ProjectIds.pittgoogle)
    )
    subscription.touch()

Pull a small batch of alerts. Helpful for testing. Not recommended for long-runnining listeners.

.. code-block:: python

    alerts = pittgoogle.pubsub.pull_batch(subscription, max_messages=4)

Open a streaming pull. Recommended for long-runnining listeners. This will pull and process
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

Delete the subscription from Google Cloud.

.. code-block:: python

    subscription.delete()

API
----

"""
import logging
import queue
from concurrent.futures import ThreadPoolExecutor
from time import sleep
from typing import Any, ByteString, Callable, List, Optional, Union

from attrs import converters, define, field
from attrs.validators import gt, instance_of, is_callable, optional
from google.api_core.exceptions import NotFound
from google.cloud import pubsub_v1

from .auth import Auth
from .exceptions import OpenAlertError
from .utils import Cast

LOGGER = logging.getLogger(__name__)


def msg_callback_example(alert: "Alert") -> "Response":
    print(f"processing message: {alert.metadata['message_id']}")
    return Response(ack=True, result=alert.dict)


def batch_callback_example(batch: list) -> None:
    oids = set(alert.dict["objectId"] for alert in batch)
    print(f"num oids: {len(oids)}")
    print(f"batch length: {len(batch)}")


@define
class Topic:
    """Basic attributes of a Pub/Sub topic.

    Parameters
    ------------
    name : `str`
        Name of the Pub/Sub topic.
    projectid : `str`
        The topic owner's Google Cloud project ID. Note: :attr:`pittgoogle.utils.ProjectIds`
        is a registry containing Pitt-Google's project IDs.
    """

    name: str = field()
    projectid: str = field()

    @property
    def path(self) -> str:
        """Fully qualified path to the topic."""
        return f"projects/{self.projectid}/topics/{self.name}"

    @classmethod
    def from_path(cls, path) -> "Topic":
        """Parse the `path` and return a new `Topic`."""
        _, projectid, _, name = path.split("/")
        return cls(name, projectid)


@define
class Subscription:
    """Basic attributes of a Pub/Sub subscription and methods to manage it.

    Parameters
    -----------
    name : `str`
        Name of the Pub/Sub subscription.
    auth : :class:`pittgoogle.auth.Auth`, optional
        Credentials for the Google Cloud project that owns this subscription. If not provided,
        it will be created from environment variables.
    topic : :class:`pittgoogle.pubsub.Topic`, optional
        Topic this subscription should be attached to. Required only when the subscription needs
        to be created.
    client : `pubsub_v1.SubscriberClient`, optional
        Pub/Sub client that will be used to access the subscription. This kwarg is useful if you
        want to reuse a client. If None, a new client will be created.
    """

    name: str = field()
    auth: Auth = field(factory=Auth, validator=instance_of(Auth))
    topic: Optional[Topic] = field(default=None, validator=optional(instance_of(Topic)))
    _client: Optional[pubsub_v1.SubscriberClient] = field(
        default=None, validator=optional(instance_of(pubsub_v1.SubscriberClient))
    )

    @property
    def projectid(self) -> str:
        """Subscription owner's Google Cloud project ID."""
        return self.auth.GOOGLE_CLOUD_PROJECT

    @property
    def path(self) -> str:
        """Fully qualified path to the subscription."""
        return f"projects/{self.projectid}/subscriptions/{self.name}"

    @property
    def client(self) -> pubsub_v1.SubscriberClient:
        """Pub/Sub client that will be used to access the subscription. If not provided, a new
        client will be created using `self.auth.credentials`.
        """
        if self._client is None:
            self._client = pubsub_v1.SubscriberClient(credentials=self.auth.credentials)
        return self._client

    def touch(self) -> None:
        """Test the connection to the subscription, creating it if necessary.

        Note that messages published to the topic before the subscription was created are
        not available to the subscription.

        Raises
        ------
        `TypeError`
            if the subscription needs to be created but no topic was provided.

        `NotFound`
            if the subscription needs to be created but the topic does not exist in Google Cloud.

        `AssertionError`
            if the subscription exists but it is not attached to self.topic and self.topic is not None.
        """
        try:
            subscrip = self.client.get_subscription(subscription=self.path)
            LOGGER.info(f"subscription exists: {self.path}")

        except NotFound:
            subscrip = self._create()
            LOGGER.info(f"subscription created: {self.path}")

        self._validate_topic(subscrip.topic)

    def _create(self) -> pubsub_v1.types.Subscription:
        if self.topic is None:
            raise TypeError("The subscription needs to be created but no topic was provided.")

        try:
            return self.client.create_subscription(name=self.path, topic=self.topic.path)

        # this error message is not very clear. let's help.
        except NotFound as nfe:
            raise NotFound(f"The topic does not exist: {self.topic.path}") from nfe

    def _validate_topic(self, connected_topic_path) -> None:
        if (self.topic is not None) and (connected_topic_path != self.topic.path):
            raise AssertionError(
                f"The subscription is attached to topic {connected_topic_path}. Expected {self.topic.path}"
            )
        self.topic = Topic.from_path(connected_topic_path)
        LOGGER.debug("topic validated")

    def delete(self) -> None:
        """Delete the subscription."""
        try:
            self.client.delete_subscription(subscription=self.path)
        except NotFound:
            LOGGER.info(f"nothing to delete. subscription not found: {self.path}")
        else:
            LOGGER.info(f"deleted subscription: {self.path}")


@define()
class Consumer:
    """Consumer class to pull a Pub/Sub subscription and process messages.

    Parameters
    -----------
    subscription : `str` or :class:`pittgoogle.pubsub.Subscription`
        Pub/Sub subscription to be pulled (it must already exist in Google Cloud).
    msg_callback : `callable`
        Function that will process a single message. It should accept a
        :class:`pittgoogle.pubsub.Alert` and return a :class:`pittgoogle.pubsub.Response`.
    batch_callback : `callable`, optional
        Function that will process a batch of results. It should accept a list of the results
        returned by the `msg_callback`.
    batch_maxn : `int`, optional
        Maximum number of messages in a batch. This has no effect if `batch_callback` is None.
    batch_maxwait : `int`, optional
        Max number of seconds to wait between messages before before processing a batch.
        This has no effect if `batch_callback` is None.
    max_backlog : `int`, optional
        Maximum number of pulled but unprocessed messages before pausing the pull.
    max_workers : `int`, optional
        Maximum number of workers for the `executor`. This has no effect if an `executor` is provided.
    executor : `concurrent.futures.ThreadPoolExecutor`, optional
        Executor to be used by the Google API to pull and process messages in the background.
    """

    _subscription: Union[str, Subscription] = field(validator=instance_of((str, Subscription)))
    msg_callback: Callable[["Alert"], "Response"] = field(validator=is_callable())
    batch_callback: Optional[Callable[[list], None]] = field(
        default=None, validator=optional(is_callable())
    )
    batch_maxn: int = field(default=100, converter=int)
    batch_maxwait: int = field(default=30, converter=int)
    max_backlog: int = field(default=1000, validator=gt(0))
    max_workers: Optional[int] = field(default=None, validator=optional(instance_of(int)))
    _executor: ThreadPoolExecutor = field(
        default=None, validator=optional(instance_of(ThreadPoolExecutor))
    )
    _queue: queue.Queue = field(factory=queue.Queue, init=False)
    streaming_pull_future: pubsub_v1.subscriber.futures.StreamingPullFuture = field(
        default=None, init=False
    )

    @property
    def subscription(self) -> Subscription:
        """Subscription to be consumed."""
        if isinstance(self._subscription, str):
            self._subscription = Subscription(self._subscription)
            self._subscription.touch()
        return self._subscription

    @property
    def executor(self) -> ThreadPoolExecutor:
        """Executor to be used by the Google API for a streaming pull."""
        if self._executor is None:
            self._executor = ThreadPoolExecutor(self.max_workers)
        return self._executor

    def stream(self, block: bool = True) -> None:
        """Open the stream in a background thread and process messages through the callbacks.

        Recommended for long-running listeners.

        Parameters
        ----------
        block : `bool`
            Whether to block the main thread while the stream is open. If `True`, block
            indefinitely (use `Ctrl-C` to close the stream and unblock). If False, open the stream
            and then return (use :meth:`~Consumer.stop()` to close the stream).
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
            flow_control=pubsub_v1.types.FlowControl(max_messages=self.max_backlog),
            scheduler=pubsub_v1.subscriber.scheduler.ThreadScheduler(executor=self.executor),
            await_callbacks_on_shutdown=True,
        )

    def _callback(self, message: pubsub_v1.types.PubsubMessage) -> None:
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
                sleep(60)

        batch, count = [], 0
        while True:
            try:
                batch.append(self._queue.get(block=True, timeout=self.batch_maxwait))

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
