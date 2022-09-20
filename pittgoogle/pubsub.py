#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""Classes to facilitate connections to Pub/Sub streams."""
# the rest of the docstring is in /docs/source/api/pubsub.rst


import logging
import os
import queue
from typing import Callable, Iterable, List, Mapping, Optional, Union

import attrs
from google.api_core.exceptions import NotFound
from google.cloud import pubsub_v1

from .auth import Auth
from .types import Alert, Response
from .utils import Cast, ProjectIds

# from google.cloud.pubsub_v1.subscriber.scheduler import ThreadScheduler
# from concurrent.futures.thread import ThreadPoolExecutor


LOGGER = logging.getLogger(__name__)


@attrs.define
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

    # name: str = attrs.field(default="ztf-loop")
    name: str
    """Name of the Pub/Sub topic."""
    # projectid: str = attrs.field(default=ProjectIds.pittgoogle)
    projectid: str
    """Topic owner's Google Cloud project ID."""

    @property
    def path(self) -> str:
        """Fully qualified path to the topic."""
        return f"projects/{self.projectid}/topics/{self.name}"

    # @path.setter
    # def path(self, value):
    #     _, self.projectid, _, self.name = value.split("/")
    #     LOGGER.info(f"Topic set to {self}")

    @staticmethod
    def from_path(path):
        """Parse `path` and return a new `Topic`."""
        _, projectid, _, name = path.split("/")
        return Topic(name, projectid)


@attrs.define
class Subscription:
    """Basic attributes of a Pub/Sub subscription plus methods to manage it.

    Parameters
    -----------
    name : `str`
        Name of the Pub/Sub subscription.
    auth : `pittgoogle.auth.Auth`
        Credentials for access to the Google Cloud project that owns this subscription.
    """

    name: str = attrs.field()
    """Name of the Pub/Sub subscription."""
    auth: Auth = attrs.field(factory=Auth, validator=attrs.validators.instance_of(Auth))
    """:class:`Auth()` with credentials for the subscription's Google Cloud project."""
    topic: Optional[Topic] = attrs.field(
        default=None,
        validator=attrs.validators.optional(attrs.validators.instance_of(Topic)),
    )
    """Topic this subscription should be attached to."""
    _client: Optional[pubsub_v1.SubscriberClient] = attrs.field(default=None)
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
        """Connect to the subscription in Google Cloud, creating it if necessary.

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
            LOGGER.info("Subscription exists")

        except NotFound:
            subscrip = self._create()
            LOGGER.info("Subscription created")

        self._validate_topic(subscrip.topic)
        LOGGER.info("Topic validated")

    def _create(self) -> pubsub_v1.types.Subscription:
        if self.topic is None:
            raise TypeError(
                "The subscription needs to be created but no topic was provided."
            )

        try:
            return self.client.create_subscription(
                name=self.path, topic=self.topic.path
            )

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

    def delete(self) -> None:
        """Delete the subscription."""
        try:
            self.client.delete_subscription(subscription=self.path)
        except NotFound:
            LOGGER.info(f"Nothing to delete. Subscription not found: {self.path}")
        else:
            LOGGER.info(f"Deleted subscription: {self.path}")

    @staticmethod
    def _from_name_idempotent(name) -> "Subscription":
        if isinstance(name, str):
            return Subscription(name)
        if isinstance(name, Subscription):
            return name
        raise TypeError("A str or pittgoogle.pubsub.Subscription is required.")


@attrs.define(kw_only=True)
class Consumer:
    """Consumer class to pull a Pub/Sub subscription and process messages.

    All parameters are keyword-only.

    Parameters
    -----------
    subscription : `Subscription` or `str`
        Pub/Sub subscription to be pulled. This must already exist in Google Cloud.
    **Callback**
    # unpack : iterable of `str`
    #     Attributes of :class:`~pittgoogle.types.Alert` that should be populated.
    #     This determines which data is available to ``callback``.
    callback : `callable`
        Function that will process a single message.
        It should accept a single :class:`pittgoogle.types.Alert` and
        return a :class:`pittgoogle.types.Response`.
    nbatch : optional, `int`
        This has no effect if `batch_callback` is None.
    batch_callback : optional, `callable`
        Function that will process a batch of results.
        It should accept a sequence of results .
    callback_kwargs : `dict`
        Keyword arguments for both ``callback`` and `batch_callback`.
    **Flow Configs**
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
    subscription: Union[str, Subscription] = attrs.field(
        # default="ztf-loop",
        # default=attrs.Factory(Subscription, takes_self=False),
        # factory=Subscription,
        converter=Subscription._from_name_idempotent,
        validator=attrs.validators.instance_of(Subscription),
    )
    """:class:`Subscription` that the consumer will pull."""
    # Flow configs
    max_results: Optional[int] = attrs.field(
        default=10,
        validator=attrs.validators.optional(attrs.validators.gt(0)),
    )
    """Maximum number of messages to pull and process before stopping."""
    timeout: int = attrs.field(
        default=30, validator=attrs.validators.optional(attrs.validators.gt(0))
    )
    """Maximum number of seconds to wait for a new message before stopping."""
    # coerced to max_backlog <= max_results by stream()
    max_backlog: int = attrs.field(default=1000, validator=attrs.validators.gt(0))
    """Maximum number of pulled but unprocessed messages before pausing the pull."""
    # Callback
    callback: Optional[Callable[[Alert], Response]] = attrs.field(
        default=None, validator=attrs.validators.optional(attrs.validators.is_callable)
    )
    """A :ref:`user callback <user callback>` or None."""
    callback_kwargs: Mapping = attrs.field(factory=dict)
    """Keyword arguments for `callback`."""
    # unpack: Iterable[str] = attrs.field(
    #     default=["dict", "metadata"],
    #     # each element must be an attribute of Alert
    #     validator=attrs.validators.deep_iterable(
    #         attrs.validators.in_(attrs.asdict(Alert()).keys())
    #     ),
    # )
    # """Attributes of :class:`~pittgoogle.types.Alert` to be populated and available."""
    # init=False
    results: list = attrs.field(factory=list, init=False)
    """Container storing values returned from ``callback``."""
    _queue: queue.Queue = attrs.field(factory=queue.Queue, init=False)
    """Queue to communicate between threads and enforce stopping conditions."""
    _block: bool = attrs.field(default=True, init=False)

    # def __attrs_post_init__(self):
    #     LOGGER.debug("Replacing the subscription's client with the consumer's client.")
    #     self.subscription.client = self.client

    def stream(self, block: bool = True) -> Optional[List]:
        """Open the stream and process messages through the :ref:`callbacks <callbacks>`.

        This starts a streaming pull on the subscription, in a background thread.
        To close the stream before stopping conditions are met,
        use `Ctrl-C` or :meth:`~Consumer.stop()` as described below.

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

        Return:
            List of results, if any, that the user callback passed back to the consumer
            via :attr:`~pittgoogle.types.Response.result`.
        """
        # tell the callback whether the consumer is actively managing the queue
        self._block = block
        # we want to run some checks just before opening the stream
        self._validate_callback()
        # if not self._confirm_no_callback():
        #     return
        self._backlog_le_results()

        # Google API has a thread scheduler that can run multiple background threads
        # self.scheduler = ThreadScheduler(ThreadPoolExecutor(max_workers))
        # self.scheduler.schedule(self.main_callback)

        # open a streaming-pull connection to the subscription
        # and process incoming messages through the callback, in a background thread
        LOGGER.info(
            f"Opening a streaming pull on subscription: {self.subscription.path}"
        )
        self._open_stream()

        if not self._block:
            LOGGER.info(
                "The stream is open in the background. "
                "Call the consumer's stop method to close it."
            )
            return

        try:
            total_count = self._manage_flow()
            self.stop()

        # We must catch all errors so we can
        # stop the streaming pull and close the background thread before raising them.
        except (KeyboardInterrupt, Exception):
            self.stop()
            raise

        LOGGER.info(
            f"Processed {total_count} messages from {self.subscription.path}. "
            "The actual number of messages that were pulled and acknowledged "
            "may be higher if the user elected not to count some messages."
        )

        # if any results were collected, return them
        if len(self.results) > 0:
            return self.results

    def _backlog_le_results(self) -> None:
        """Enforce max_backlog <= max_results."""
        if (self.max_results is not None) and (self.max_backlog > self.max_results):
            LOGGER.info(
                (
                    "Setting max_backlog = max_results to prevent an excessive number "
                    "of pulled messages that will never be processed. "
                )
            )
            self.max_backlog = self.max_results

    def _validate_callback(self) -> None:
        """Make sure the user submitted a valid callback."""
        if self.callback is None:
            proceed = input(
                (
                    "Warning: No callback provided. "
                    "If you proceed, messages will be acknowledged to Pub/Sub "
                    "but not stored locally -- thus they will be lost. "
                    "\n\nDo you want to proceed? (yes/no)\n\n"
                )
            )

            if proceed in ["Y", "y", "yes", "Yes"]:
                self.callback = self._count_alert

            else:
                raise AttributeError(name="callback", obj=self)

    def _count_alert(self) -> Response:
        """Return a :class:`Response` indicating the message should be ack'd and counted."""
        return Response(ack=True, result=None)

    def _open_stream(self) -> None:
        self.streaming_pull_future = self.client.client.subscribe(
            self.subscription.path,
            self.main_callback,
            flow_control=pubsub_v1.types.FlowControl(max_messages=self.max_backlog),
            # scheduler=self.scheduler,
            # await_callbacks_on_shutdown=True,
        )

    def _manage_flow(self) -> int:
        """Control the flow, return when stopping conditions are met."""
        total_count = 0
        while True:
            try:
                total_count += self._queue.get(block=True, timeout=self.timeout)

            except queue.Empty:
                LOGGER.info("Timeout stopping condition reached.")
                break

            else:
                self._queue.task_done()

                if (self.max_results) & (total_count >= self.max_results):
                    LOGGER.info("Max results stopping condition reached.")
                    break

        return total_count

    def main_callback(self, message: pubsub_v1.types.PubsubMessage) -> None:
        """Unpack the message, run the :attr:`~Consumer.callback` and handle the response."""
        response = self.callback(Alert(msg=message), **self.callback_kwargs)  # Response

        if response._store:
            self.results.append(response.result)

        if response.ack:
            message.ack()
        else:
            message.nack()

        # Communicate with the main thread
        if self._block:
            self._queue.put(response._count)
            if self.max_results is not None:
                # block until main thread acknowledges so we don't ack msgs that get lost
                self._queue.join()  # single background thread => one-in-one-out

    # def handle_result(self, response: Response) -> int:
    #     """Store a result if requested. Re."""
    #     # if response.result == False, don't count and don't store
    #     if isinstance(response.result, bool) and not response.result:
    #         count = 0
    #
    #     else:
    #         count = 1
    #         if response.result is not None:
    #             self.results.append(response.result)
    #
    #     # elif response.result is None:
    #     #     # count, don't store
    #     #     count = 1
    #     #
    #     # else:
    #     #     # count, store
    #     #     count = 1
    #     #     self.results.append(response.result)
    #
    #     return count

    def stop(self) -> None:
        """Shutdown the streaming pull and exit the background thread gracefully."""
        LOGGER.info("Closing the stream.")
        self.streaming_pull_future.cancel()  # Trigger the shutdown.
        self.streaming_pull_future.result()  # Block until the shutdown is complete.
