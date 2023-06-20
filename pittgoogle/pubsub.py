#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""Classes to facilitate connections to Pub/Sub streams.

Stream block param
:param block: Whether to block the foreground thread while the stream is open.
    If True (default), the consumer manages the flow of messages using a
    `Queue` and enforces the stopping conditions
    (``max_messages``, ``timeout``).
    Use `Ctrl-C` at any time to close the stream and unblock the terminal.

    If False, returns immediately after opening the stream.
    Use this with caution.
    The pull will continue in the background, but the consumer will not
    enforce the stopping conditions -- thus it can run indefinitely.
    Stop it manually with :meth:`~Consumer.stop()`.

    If this (block=False) is the desired behavior,
    consider calling the Pub/Sub API directly.
    You will have more control over the pull, including the option
    to parallelize.
    The command is
    `google.cloud.pubsub_v1.subscriber.client.Client.subscribe() <https://googleapis.dev/python/pubsub/latest/subscriber/api/client.html#google.cloud.pubsub_v1.subscriber.client.Client.subscribe>`__.
    You can call it using the consumer's underlying Pub/Sub ``Client``:

    .. code-block:: python

        from pittgoogle import pubsub

        consumer = pubsub.Consumer()

        # consumer.client.client is a
        # google.cloud.pubsub_v1.subscriber.client.Client()
        # Call its subscribe() method to start a streaming pull
        # (include desired args/kwargs):

        consumer.streaming_pull_future = consumer.client.client.subscribe()

    Assigning the result to ``consumer.streaming_pull_future``
    allows you to use the Pitt-Google ``consumer`` to stop the streaming pull
    and exit the background thread gracefully:

    .. code-block:: python

        consumer.stop()
"""
# the rest of the docstring is in /docs/source/api/pubsub.rst
import logging
import queue
from concurrent.futures import ThreadPoolExecutor
from time import sleep
from typing import Callable, List, Optional, Union

from attrs import define, field, validators
from google.api_core.exceptions import NotFound
from google.cloud import pubsub_v1

from .auth import Auth
from .types import Alert, Response

LOGGER = logging.getLogger(__name__)


@define
class Topic:
    """Basic attributes of a Pub/Sub topic.

    Parameters
    ------------
    name : `str`
        Name of the Pub/Sub topic.
    projectid : `str`
        The topic owner's Google Cloud project ID.
        Note: :attr:`pittgoogle.utils.ProjectIds` is a registry containing project IDs.
    """

    name: str = field()
    """Name of the Pub/Sub topic."""
    projectid: str = field()
    """Topic owner's Google Cloud project ID."""

    @property
    def path(self) -> str:
        """Fully qualified path to the topic."""
        return f"projects/{self.projectid}/topics/{self.name}"

    @staticmethod
    def from_path(path) -> "Topic":
        """Parse `path` and return a new `Topic`."""
        _, projectid, _, name = path.split("/")
        return Topic(name, projectid)


@define
class Subscription:
    """Basic attributes of a Pub/Sub subscription plus methods to manage it.

    Parameters
    -----------
    name : `str`
        Name of the Pub/Sub subscription.
    auth : `pittgoogle.auth.Auth`
        Credentials for access to the Google Cloud project that owns this subscription.
    """

    name: str = field()
    """Name of the Pub/Sub subscription."""
    auth: Auth = field(factory=Auth, validator=validators.instance_of(Auth))
    """:class:`Auth()` with credentials for the subscription's Google Cloud project."""
    topic: Optional[Topic] = field(
        default=None,
        validator=validators.optional(validators.instance_of(Topic)),
    )
    """Topic this subscription should be attached to."""
    _client: Optional[pubsub_v1.SubscriberClient] = field(default=None)
    """Pub/Sub client that will be used to access the subscription."""

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
        """`pubsub_v1.SubscriberClient` instance.

        The client is authenticated using `self.auth.credentials`.
        """
        if self._client is None:
            self._client = pubsub_v1.SubscriberClient(credentials=self.auth.credentials)
        return self._client

    def touch(self, topic: Optional[Topic] = None) -> None:
        """Test the connection to the subscription, creating it if necessary.

        Note that messages published to the topic before the subscription is created are
        not available.

        Parameters
        -----------
        topic : optional, `Topic`
            If not None, self.topic will be set to this value before anything else happens.

        Raises
        ------
        TypeError if the subscription needs to be created but no topic was provided.

        AssertionError if the subscription exists but it is not attached to self.topic,
        and self.topic is not None.

        NotFound
        """
        if topic is not None:
            self.topic = topic

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

    def _validate_topic(self, connected_topic_path):
        if (self.topic is not None) and (connected_topic_path != self.topic.path):
            raise AssertionError(
                f"Subscription is not attached to the expected topic. "
                f"Subscription topic: {connected_topic_path}. Expected topic: {self.topic.path}."
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


def msg_callback_example(alert: Alert) -> Response:
    print(f"msgid: {alert.metadata['message_id']}")
    return Response(ack=True, result=alert)


def batch_callback_example(batch: list) -> None:
    # oids = set(alert.dict["objectId"] for alert in batch)
    # print(f"num oids: {len(oids)}")
    print(f"batch length: {len(batch)}")


@define(kw_only=True)
class Consumer:
    """Consumer class to pull a Pub/Sub subscription and process messages.

    All parameters are keyword-only.

    Parameters
    -----------
    subscription : `Subscription` or `str`
        Pub/Sub subscription to be pulled. This must already exist in Google Cloud.
    msg_callback : `callable`
        Function that will process a single message.
        It should accept a single :class:`pittgoogle.types.Alert` and
        return a :class:`pittgoogle.types.Response`.
    nbatch : optional, `int`
        This has no effect if `batch_callback` is None.
    batch_callback : optional, `callable`
        Function that will process a batch of results.
        It should accept a sequence of results .
    callback_kwargs : `dict`
        Keyword arguments for both ``msg_callback`` and `batch_callback`.
    max_results : optional, `int`
        Maximum number of messages to pull and process before stopping.
        Use None for no limit.
    timeout : optional, `int`
        Maximum number of seconds to wait for a new message before stopping.
        Use None for no limit.
    max_backlog : optional, `int`
        Maximum number of pulled but unprocessed messages to hold
        before pausing the streaming pull.
        This will be coerced to satisfy ``max_backlog <= max_results``.
    """

    # Connection
    _subscription: Union[str, Subscription] = field(
        validator=validators.instance_of((str, Subscription))
    )
    """:class:`Subscription` that the consumer will pull."""
    # Flow configs
    max_backlog: int = field(default=1000, validator=validators.gt(0))
    """Maximum number of pulled but unprocessed messages before pausing the pull."""
    # Scheduler
    max_workers: Optional[int] = field(
        default=None, validator=validators.optional(validators.instance_of(int))
    )
    _executor: ThreadPoolExecutor = field(
        default=None, validator=validators.optional(validators.instance_of(ThreadPoolExecutor))
    )
    # Callbacks
    msg_callback: Callable[[Alert], Response] = field(validator=validators.is_callable())
    """Callback for an individual message."""
    batch_callback: Optional[Callable[[list], None]] = field(
        default=None, validator=validators.optional(validators.is_callable())
    )
    """Callback for a batch of messages."""
    batch_maxn: int = field(default=100, converter=int)
    """Max number of messages in a batch."""
    batch_maxwait: int = field(default=30, converter=int)
    """Max time to wait in seconds for a single message before processing a batch."""
    _queue: queue.Queue = field(factory=queue.Queue, init=False)
    """Queue to communicate between threads."""
    streaming_pull_future: pubsub_v1.subscriber.futures.StreamingPullFuture = field(
        default=None, init=False
    )

    @property
    def subscription(self):
        if isinstance(self._subscription, str):
            self._subscription = Subscription(self._subscription)
            self._subscription.touch()
        return self._subscription

    @property
    def executor(self):
        if self._executor is None:
            self._executor = ThreadPoolExecutor(self.max_workers)
        return self._executor

    def stream(self, block: bool = True) -> Optional[List]:
        """Open the stream and process messages through the :ref:`callbacks <callbacks>`."""
        # open a streaming-pull and process messages through the callback, in the background
        self.open_stream()

        if not block:
            msg = "The stream is open in the background. Use consumer.stop() to close it."
            print(msg)
            LOGGER.info(msg)
            return

        try:
            self.process_batches()

        # catch all exceptions and attempt to close the stream before raising
        except (KeyboardInterrupt, Exception):
            self.stop()
            raise

    def open_stream(self) -> None:
        LOGGER.info(f"opening a streaming pull on subscription: {self.subscription.path}")
        self.streaming_pull_future = self.subscription.client.subscribe(
            self.subscription.path,
            self.callback,
            flow_control=pubsub_v1.types.FlowControl(max_messages=self.max_backlog),
            scheduler=pubsub_v1.subscriber.scheduler.ThreadScheduler(executor=self.executor),
            await_callbacks_on_shutdown=True,
        )

    def callback(self, message: pubsub_v1.types.PubsubMessage) -> None:
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

    def process_batches(self) -> None:
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

            else:
                self._queue.task_done()
                count += 1

            if count == self.batch_maxn:
                # hit the max number of results. process the batch
                self.batch_callback(batch)
                batch, count = [], 0

    def stop(self) -> None:
        """Attempt to shutdown the streaming pull and exit the background thread gracefully."""
        LOGGER.info("closing the stream")
        self.streaming_pull_future.cancel()  # Trigger the shutdown.
        self.streaming_pull_future.result()  # Block until the shutdown is complete.
