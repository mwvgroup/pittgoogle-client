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
import importlib.resources
import io
import json
import logging
import queue
from concurrent.futures import ThreadPoolExecutor
from time import sleep
from typing import TYPE_CHECKING, Any, Callable, List, Optional, Union

import fastavro
import yaml
from attrs import converters, define, field
from attrs.validators import gt, instance_of, is_callable, optional
from google.api_core.exceptions import NotFound
from google.cloud import pubsub_v1

from .auth import Auth
from .exceptions import OpenAlertError
from .utils import Cast

if TYPE_CHECKING:
    import google.protobuf.timestamp_pb2
    import google._upb._message
    import pandas as pd


LOGGER = logging.getLogger(__name__)
PACKAGE_DIR = importlib.resources.files(__package__)


def msg_callback_example(alert: "Alert") -> "Response":
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
    """Pull a single batch of messages from the `subscription`.

    Parameters
    ----------
    subscription : `str` or :class:`pittgoogle.pubsub.Subscription`
        Subscription to be pulled. If `str`, the name of the subscription.
    max_messages : `int`
        Maximum number of messages to be pulled.
    schema_name : `str`
        One of "ztf", "ztf.lite", "elasticc.v0_9_1.alert", "elasticc.v0_9_1.brokerClassification".
        Schema name of the alerts in the subscription. Passed to :class:`pittgoogle.pubsub.Alert`
        for unpacking. If not provided, some properties of the `Alert` may not be available.
    subscription_kwargs
        Keyword arguments sent to :class:`pittgoogle.pubsub.Subscription`.
        Ignored if `subscription` is a :class:`pittgoogle.pubsub.Subscription`.
    """
    if isinstance(subscription, str):
        subscription = Subscription(subscription, **subscription_kwargs)

    response = subscription.client.pull(
        {"subscription": subscription.path, "max_messages": max_messages}
    )

    alerts = [
        Alert.from_msg(msg.message, schema_name=schema_name) for msg in response.received_messages
    ]

    ack_ids = [msg.ack_id for msg in response.received_messages]
    if len(ack_ids) > 0:
        subscription.client.acknowledge({"subscription": subscription.path, "ack_ids": ack_ids})

    return alerts


@define
class Topic:
    """Basic attributes of a Pub/Sub topic.

    Parameters
    ------------
    name : `str`
        Name of the Pub/Sub topic.
    projectid : `str`, optional
        The topic owner's Google Cloud project ID. Either this or `auth` is required. Use this
        if you are connecting to a subscription owned by a different project than this topic. Note:
        :attr:`pittgoogle.utils.ProjectIds` is a registry containing Pitt-Google's project IDs.
    auth : :class:`pittgoogle.auth.Auth`, optional
        Credentials for the Google Cloud project that owns this topic. If not provided,
        it will be created from environment variables when needed.
    client : `pubsub_v1.PublisherClient`, optional
        Pub/Sub client that will be used to access the topic. If not provided, a new client will
        be created (using `auth`) the first time it is requested.
    """

    name: str = field()
    projectid: str = field(default=None)
    _auth: Auth = field(default=None, validator=optional(instance_of(Auth)))
    _client: Optional[pubsub_v1.PublisherClient] = field(
        default=None, validator=optional(instance_of(pubsub_v1.PublisherClient))
    )

    @classmethod
    def from_path(cls, path) -> "Topic":
        """Parse the `path` and return a new `Topic`."""
        _, projectid, _, name = path.split("/")
        return cls(name, projectid)

    @property
    def auth(self) -> Auth:
        """Credentials for the Google Cloud project that owns this topic.

        This will be created from environment variables if `self._auth` is None.
        """
        if self._auth is None:
            self._auth = Auth()

        if (self.projectid != self._auth.GOOGLE_CLOUD_PROJECT) and (self.projectid is not None):
            LOGGER.warning(f"setting projectid to match auth: {self._auth.GOOGLE_CLOUD_PROJECT}")
        self.projectid = self._auth.GOOGLE_CLOUD_PROJECT

        return self._auth

    @property
    def path(self) -> str:
        """Fully qualified path to the topic."""
        # make sure we have a projectid. if it needs to be set, call auth
        if self.projectid is None:
            self.auth
        return f"projects/{self.projectid}/topics/{self.name}"

    @property
    def client(self) -> pubsub_v1.PublisherClient:
        """Pub/Sub client for topic access.

        Will be created using `self.auth.credentials` if necessary.
        """
        if self._client is None:
            self._client = pubsub_v1.PublisherClient(credentials=self.auth.credentials)
        return self._client

    def touch(self) -> None:
        """Test the connection to the topic, creating it if necessary."""
        try:
            self.client.get_topic(topic=self.path)
            LOGGER.info(f"topic exists: {self.path}")

        except NotFound:
            self.client.create_topic(name=self.path)
            LOGGER.info(f"topic created: {self.path}")

    def delete(self) -> None:
        """Delete the topic."""
        try:
            self.client.delete_topic(topic=self.path)
        except NotFound:
            LOGGER.info(f"nothing to delete. topic not found: {self.path}")
        else:
            LOGGER.info(f"deleted topic: {self.path}")

    def publish(self, alert: "Alert", format="json") -> int:
        """Publish the `alert.dict` in the requested `format`, attaching the `alert.attributes`."""
        if format == "json":
            message = json.dumps(alert.dict).encode("utf-8")

        elif format.startswith("elasticc"):
            # load the avro schema and use it to serialize alert.dict
            schema = fastavro.schema.load_schema(PACKAGE_DIR / f"schemas/elasticc/{format}.avsc")
            fout = io.BytesIO()
            fastavro.schemaless_writer(fout, schema, alert.dict)
            fout.seek(0)
            message = fout.getvalue()

        # attribute keys and values must be strings
        attributes = {str(key): str(val) for key, val in alert.attributes.items()}

        future = self.client.publish(self.path, data=message, **attributes)
        return future.result()


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
    schema_name : `str`
        One of "ztf", "ztf.lite", "elasticc.v0_9_1.alert", "elasticc.v0_9_1.brokerClassification".
        Schema name of the alerts in the subscription. Passed to :class:`pittgoogle.pubsub.Alert`
        for unpacking. If not provided, some properties of the `Alert` may not be available.
    """

    name: str = field()
    auth: Auth = field(factory=Auth, validator=instance_of(Auth))
    topic: Optional[Topic] = field(default=None, validator=optional(instance_of(Topic)))
    _client: Optional[pubsub_v1.SubscriberClient] = field(
        default=None, validator=optional(instance_of(pubsub_v1.SubscriberClient))
    )
    schema_name: str = field(factory=str)

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

    def pull_batch(self, max_messages: int = 1) -> List["Alert"]:
        """Pull a single batch of messages.

        Recommended for testing. Not recommended for long-running listeners (use the
        :meth:`~Consumer.stream` method instead).

        Parameters
        ----------
        max_messages : `int`
            Maximum number of messages to be pulled.
        """
        return pull_batch(self, max_messages=max_messages, schema_name=self.schema_name)


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

    def pull_batch(self, max_messages: int = 1) -> List["Alert"]:
        """Pull a single batch of messages.

        Recommended for testing. Not recommended for long-running listeners (use the
        :meth:`~Consumer.stream` method instead).

        Parameters
        ----------
        max_messages : `int`
            Maximum number of messages to be pulled.
        """
        return self.subscription.pull_batch(max_messages=max_messages)


@define(kw_only=True)
class Alert:
    """Pitt-Google container for a Pub/Sub message.

    Typical usage is to instantiate an `Alert` using only a `msg`, and then the other attributes
    will be automatically extracted and returned (lazily).

    All parameters are keyword only.

    Parameters
    ------------
    bytes : `bytes`, optional
        The message payload, as returned by Pub/Sub. It may be Avro or JSON serialized depending
        on the topic.
    dict : `dict`, optional
        The message payload as a dictionary.
    metadata : `dict`, optional
        The message metadata.
    msg : `google.cloud.pubsub_v1.types.PubsubMessage`, optional
        The Pub/Sub message object, documented at
        `<https://cloud.google.com/python/docs/reference/pubsub/latest/google.cloud.pubsub_v1.types.PubsubMessage>`__.
    schema_name : `str`
        One of "ztf", "ztf.lite", "elasticc.v0_9_1.alert", "elasticc.v0_9_1.brokerClassification".
        Schema name of the alert. Used for unpacking. If not provided, some properties of the
        `Alert` may not be available.
    """

    # _bytes: Optional[ByteString] = field(default=None)
    _dict: Optional[dict] = field(default=None)
    _attributes: Optional[Union[dict, "google._upb._message.ScalarMapContainer"]] = field(
        default=None
    )
    # _metadata: Optional[dict] = field(default=None)
    msg: Optional[Union["pubsub_v1.types.PubsubMessage", "_PubsubMessageLike"]] = field(
        default=None
    )
    """Incoming Pub/Sub message object."""
    _dataframe: Optional["pd.DataFrame"] = field(default=None)
    schema_name: str = field(factory=str)
    _schema_map: Optional[dict] = field(default=None)
    # _metadata: Optional[dict] = field(default=None)

    @classmethod
    def from_msg(cls, msg, schema_name=str()):  # [TODO] update tom_desc to use this
        """Create an `Alert` from a `pubsub_v1.types.PubsubMessage`."""
        return cls(msg=msg, schema_name=schema_name)

    @classmethod
    def from_cloud_run(cls, envelope, schema_name=str()):
        return cls(
            msg=_PubsubMessageLike(
                data=envelope["message"]["data"],
                attributes=envelope["message"]["attributes"],
                message_id=envelope["message"]["message_id"],
                publish_time=envelope["message"]["publish_time"],
                ordering_key=envelope["message"]["ordering_key"],
            ),
            schema_name=schema_name,
        )

    # @property
    # def bytes(self) -> bytes:
    #     """Message payload in original format (Avro or JSON serialized bytes)."""
    #     if self._bytes is None:
    #         # add try-except when we know what we're looking for
    #         self._bytes = self.msg.data
    #         if self._bytes is None:
    #             # if we add a "path" attribute for the path to an avro file on disk
    #             # we can load it like this:
    #             #     with open(self.path, "rb") as f:
    #             #         self._bytes = f.read()
    #             pass
    #     return self._bytes

    @property
    def dict(self) -> dict:
        """Message payload as a dictionary. Created from `self.msg.data` and `self.schema_name`, if needed.

        Raises
        ------
        :class:`pittgoogle.exceptions.OpenAlertError`
            if unable to deserialize the alert bytes.
        """
        if self._dict is not None:
            return self._dict

        if self.schema_name.startswith("elasticc"):
            # self.msg.data is avro and schemaless. load the schema, then convert the bytes to a dict
            schemapath = PACKAGE_DIR / f"schemas/elasticc/{self.schema_name}.avsc"
            schema = fastavro.schema.load_schema(schemapath)
            with io.BytesIO(self.msg.data) as fin:
                self._dict = fastavro.schemaless_reader(fin, schema)
            return self._dict

        if self.schema_name == "":
            LOGGER.warning("no alert schema_name provided. attempting to deserialize without it.")

        # assume this is a ztf or ztf-lite alert
        # this should be rewritten to catch specific errors
        # for now, just try avro then json, catching basically all errors in the process
        try:
            self._dict = Cast.avro_to_dict(self.msg.data)
        except Exception:
            try:
                self._dict = Cast.json_to_dict(self.msg.data)
            except Exception:
                raise OpenAlertError("failed to deserialize the alert bytes")
        return self._dict

    @property
    def attributes(self) -> Union[dict, "google._upb._message.ScalarMapContainer"]:
        """Custom metadata for the message. Pub/Sub handles this as a dict-like called "attributes".

        If None, this will be set to `self.msg.attributes`.
        Update as desired.
        When publishing, this will be sent as the message attributes.
        """
        if self._attributes is None:
            self._attributes = self.msg.attributes
        return self._attributes

    @property
    def dataframe(self) -> "pd.DataFrame":
        if self._dataframe is None:
            import pandas as pd  # lazy-load pandas. it hogs memory on cloud functions and run

            if self.schema_name.endswith(".lite"):
                src_df = pd.DataFrame(self.dict["source"], index=[0])
                prvs_df = pd.DataFrame(self.dict["prvSources"])
            else:
                src_df = pd.DataFrame(self.dict[self.schema_map["source"]], index=[0])
                prvs_df = pd.DataFrame(self.dict[self.schema_map["prvSources"]])
            self._dataframe = pd.concat([src_df, prvs_df], ignore_index=True)

        return self._dataframe

    @property
    def schema_map(self) -> dict:
        if self._schema_map is None:
            if self.schema_name == str():
                raise TypeError("no alert schema_name provided. unable to load schema map.")
            survey = self.schema_name.split(".")[0]
            path = PACKAGE_DIR / f"schema_maps/{survey}.yml"
            self._schema_map = yaml.safe_load(path.read_text())
        return self._schema_map

    # @property
    # def metadata(self) -> dict:
    #     """Pub/Sub message metadata.

    #     Includes

    #         - message_id, publish_time, and ordering_key* of the incoming Pub/Sub message
    #         - attributes, which is a dict that typically includes the attributes of the
    #           incoming message and possibly additional entries added by the user in the meantime.

    #     *To be useful, ordering_key requires that ordering is enabled on the subscription.
    #     """
    #     if self._metadata is None:
    #         self._metadata = {
    #             "message_id": self.msg.message_id,
    #             "publish_time": self.msg.publish_time,
    #             # ordering must be enabled on the subscription for this to be useful
    #             "ordering_key": self.msg.ordering_key,
    #             # [TODO] breaking change. attributes is now a dict. open a pr on tom_desc
    #             # typically includes self.msg.attributes plus additional items added by the user
    #             "attributes": self.attributes,
    #         }
    #     return self._metadata


@define(kw_only=True, frozen=True)
class Response:
    """Container for a response, to be returned by a :meth:`pittgoogle.pubsub.Consumer.msg_callback`.

    Parameters
    ------------
    ack : `bool`
        Whether to acknowledge the message. Use `True` if the message was processed successfully,
        `False` if an error was encountered and you would like Pub/Sub to redeliver the message at
        a later time. Note that once a message is acknowledged to Pub/Sub it is permanently deleted
        (unless the subscription has been explicitly configured to retain acknowledged messages).

    result : `Any`
        Anything the user wishes to return. If not `None`, the Consumer will collect the results
        in a list and pass the list to the user's batch callback for further processing.
        If there is no batch callback the results will be lost.
    """

    ack: bool = field(default=True, converter=converters.to_bool)
    result: Any = field(default=None)


@define(frozen=True)
class _PubsubMessageLike:
    """Container for an incoming Pub/Sub message that mimics a `pubsub_v1.types.PubsubMessage`.

    It is convenient for the `Alert` class to work with a message as a
    `pubsub_v1.types.PubsubMessage`. However, there are many ways to obtain an alert that do
    not result in a `pubsub_v1.types.PubsubMessage` (e.g., an alert packet loaded from disk or
    an incoming message to a Cloud Functions or Cloud Run module). In those cases, this class
    is used to create an object with the same attributes as a `pubsub_v1.types.PubsubMessage`.
    This object is then assigned to the `msg` attribute of the `Alert`.
    """

    data: bytes = field()
    attributes: dict = field(factory=dict)
    message_id: Optional[str] = field(default=None)
    publish_time: Optional["google.protobuf.timestamp_pb2.Timestamp"] = field(default=None)
    ordering_key: Optional[str] = field(default=None)
