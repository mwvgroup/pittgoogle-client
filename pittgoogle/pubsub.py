#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""Classes to facilitate connections to Pub/Sub streams."""
# the rest of the docstring is in /docs/source/api/pubsub.rst


import dataclasses
import inspect
import logging
import os
import queue
from typing import Callable, Iterable, List, Mapping, Optional, Union

import attrs
from google.api_core.exceptions import NotFound
from google.cloud import pubsub_v1

from .auth import Auth
from .types import Alert, Response
from .utils import Cast, PittGoogleProjectIds, init_defaults

# from google.cloud.pubsub_v1.subscriber.scheduler import ThreadScheduler
# from concurrent.futures.thread import ThreadPoolExecutor


LOGGER = logging.getLogger(__name__)


# @dataclasses.dataclass
@attrs.define
class Topic:
    """Basic attributes of a Pub/Sub topic.

    Parameters
    ------------
    name : `str`
        Name of the Pub/Sub topic.
    projectid : `str`
        The topic owner's Google Cloud project ID.
        Note that Pitt-Google's IDs can be
        obtained from :attr:`pittgoogle.utils.PittGoogleProjectIds.production`,
        :attr:`pittgoogle.utils.PittGoogleProjectIds.testing`, etc.
    """

    name: str = attrs.field(
        default="ztf-loop", validator=attrs.validators.instance_of(str)
    )
    """Name of the Pub/Sub topic."""
    projectid: str = attrs.field(
        default=PittGoogleProjectIds.production,
        validator=attrs.validators.instance_of(str),
    )
    """Topic owner's Google Cloud project ID."""

    @property
    def path(self) -> str:
        """Fully qualified path to the topic."""
        return f"projects/{self.projectid}/topics/{self.name}"

    @path.setter
    def path(self, value):
        _, self.projectid, _, self.name = value.split("/")
        LOGGER.info(f"Topic set to {self}")


# @dataclasses.dataclass
@attrs.define
class SubscriberClient:
    """Wrapper for a `pubsub_v1.SubscriberClient`.

    Parameters
    ------------
    auth : optional, `pittgoogle.auth.Auth`
        Authentication information for the client.
        Passing a `SubscriberClient` is idempotent.
        The API call triggering authentication with Google Cloud is not made until
        the auth's ``credentials`` or `session` attribute is explicitly requested.
    """

    _auth: Optional[Auth] = None
    _client: Optional = attrs.field(default=None, init=False)

    # def __attrs_post_init__(self):
    #     # self, auth: Union[Auth, AuthSettings, "SubscriberClient", None] = None
    #     # ):
    #     # initialization should be idempotent. unpack settings
    #     if isinstance(self._auth, SubscriberClient):
    #         client = attrs.evolve(self._auth)  # copy so can iterate and set vals
    #         for key, val in attrs.asdict(client).items():
    #             setattr(self, key, val)
    #
    #     else:
    #         self.auth = self._auth

    # authentication
    @property
    def auth(self) -> Auth:
        """:class:`pittgoogle.auth.Auth` instance for client authentication.

        If this is set to None, a default :class:`~pittgoogle.auth.Auth` will be
        created.

        Settings this manually will trigger reinstantiation of `self.client`.
        """
        if self._auth is None:
            LOGGER.info("No pittgoogle.auth.Auth supplied. Creating default.")
            self._auth = Auth()
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
        """`pubsub_v1.SubscriberClient` instance.

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


# @dataclasses.dataclass
@attrs.define
class Subscription:
    """Basic attributes of a Pub/Sub subscription plus methods to administer it.

    Parameters
    -----------
    name : `str`
        Name of the Pub/Sub subscription.
    client : optional, `pittgoogle.pubsub.SubscriberClient`, `pittgoogle.auth.Auth`
        A subscriber client or the authentitication info required to create one.
    topic : `pittgoogle.pubsub.Topic`
        Topic that the subscription is/will be attached to.
        If the subscription exists this will be set to the topic that it is attached to.
        If the subscription needs to be created it will be attached to this topic.
        If this is None it will be set to `Topic(name)`.
    """

    name: str = attrs.field(
        default="ztf-loop", validator=attrs.validators.instance_of(str)
    )
    """Name of the Pub/Sub subscription."""
    client: Union[SubscriberClient, Auth] = attrs.field(
        factory=SubscriberClient,
        converter=_Helpers.client_from_auth,
        validator=attrs.validators.instance_of(SubscriberClient),
    )
    """:class:`SubscriberClient()` to manage the subscription."""
    topic: Optional[Topic] = attrs.field(default=None)
    """:class:`Topic()` that the subscription is or will be attached to."""
    # _projectid: Optional[str] = attrs.field(default=None, init=False)

    def __attrs_post_init__(self):
        """Initialize the `topic` using the subscription `name`."""
        if self.topic is None:
            self.topic = Topic(self.name)
        #     self,
        #     name: str = "ztf-loop",
        #     client: Union[SubscriberClient, Auth, AuthSettings, None] = None,
        #     topic: Optional[Topic] = None,
        # ):
        #     self._name = name
        #     self._client = client
        #     self._topic = topic
        # self._projectid = None
        # if isinstance(self._client, Auth):
        #     self._client = SubscriberClient(client=self._client)

    # # name
    # @property
    # def name(self) -> str:
    #     """Name of the subscription."""
    #     if self._name is None:
    #         default = init_defaults(self)["name"]
    #         LOGGER.warning(f"No subscription name provided. Falling back to {default}.")
    #         self._name = default
    #
    #     return self._name
    #
    # @name.setter
    # def name(self, value):
    #     self._name = value
    #
    # @name.deleter
    # def name(self):
    #     self._name = None

    # projectid
    @property
    def projectid(self) -> str:
        """Subscription owner's Google Cloud project ID."""
        # if self._projectid is None:

        # get it from the client, if present
        if self.client is not None:
            projectid = getattr(self.client, "GOOGLE_CLOUD_PROJECT")
            LOGGER.debug(f"Subscription's projectid obtained from client. {projectid}")

        # get it from an environment variable
        else:
            projectid = os.getenv("GOOGLE_CLOUD_PROJECT", None)
            LOGGER.debug(
                (
                    "Subscription's projectid obtained from environment variable. "
                    f"projectid = {projectid}"
                )
            )

        return projectid

    # @projectid.setter
    # def projectid(self, value):
    #     self._projectid = value
    #
    # @projectid.deleter
    # def projectid(self):
    #     self._projectid = None

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

    # # client
    # @property
    # def client(self) -> SubscriberClient:
    #     """:class:`SubscriberClient()` to manage the subscription.
    #
    #     If this is set to a :class:`pittgoogle.auth.Auth`
    #     it will be used to instantiate a :class:`SubscriberClient`.
    #
    #     This will be required in order to connect to the subscription,
    #     but the connection is not checked during instantiation.
    #     """
    #     if self._client is None:
    #         # try to create a client using default AuthSettings
    #         LOGGER.debug(
    #             (
    #                 "No client or auth information provided. "
    #                 "Attempting to create a client using a default "
    #                 "pittgoogle.auth.AuthSettings()."
    #             )
    #         )
    #         self._client = SubscriberClient()
    #     else:
    #         # make sure we have a SubscriberClient and not just an Auth or AuthSettings
    #         self._client = SubscriberClient(self._client)
    #
    #     return self._client
    #
    # @client.setter
    # def client(self, value):
    #     if isinstance(value, Auth):
    #         self._client = SubscriberClient(value)
    #     else:
    #         self._client = value
    #
    # @client.deleter
    # def client(self):
    #     self._client = None

    # # topic
    # @property
    # def topic(self) -> Topic:
    #     """:class:`Topic` that the subscription is or will be attached to.
    #
    #     If the subscription exists this will be set to the topic that it is attached to.
    #
    #     If the subscription needs to be created it will be attached to this topic.
    #     If this is None it will fallback to the name of the subscription and the default
    #     Pitt-Google project ID.
    #     """
    #     if self._topic is None:
    #         default = Topic(self.name)
    #         LOGGER.debug(f"No topic provided. Falling back to {default}.")
    #         self._topic = default
    #
    #     return self._topic
    #
    # @topic.setter
    # def topic(self, value):
    #     self._topic = value
    #
    # @topic.deleter
    # def topic(self):
    #     self._topic = None

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
                    f"Connected to topic: {self.topic.path}\n"
                )
            )
            LOGGER.debug(
                "Updating `Subscription()` instance with corresponding `Topic()`"
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


# @dataclasses.dataclass
@attrs.define
class CallbackSettings:
    """Settings for the :ref:`callbacks <callbacks>`.

    Parameters
    ----------
    user_callback : callable
        A function, supplied by the user, that accepts a single
        :class:`pittgoogle.types.Alert` as
        its sole argument and returns a :class:`pittgoogle.types.Response`.
        The function is allowed to accept arbitrary keyword arguments, but their
        values must be passed to the consumer via the `user_kwargs` setting prior
        to starting the pull.
        See :ref:`user callback <user callback>` for more information.
    user_kwargs : `dict`
        A dictionary of key/value pairs that will be sent as kwargs to the
        ``user_callback`` by the consumer.
    unpack : iterable of `str`
        :class:`~pittgoogle.types.Alert` attributes that should be populated with data.
        This determines which data is available to the user callback.
    """

    user_callback: Optional[Callable[[Alert], Response]] = None
    user_kwargs: Optional[Mapping] = None
    unpack: Iterable[str] = tuple(["dict", "metadata"])


# @dataclasses.dataclass
@attrs.define
class FlowConfigs:
    """Stopping conditions and flow control settings for a streaming pull.

    Parameters
    ----------
    max_results : optional, `int`
        Maximum number of messages to pull and process before stopping.
        Default = 10, use None for no limit.
    timeout : optional, `int`
        Maximum number of seconds to wait for a new message before stopping.
        Default = 30. Use None for no limit.
    max_backlog : optional, `int`
        Maximum number of pulled but unprocessed messages before pausing the pull.
        Default = min(1000, ``max_results``).
        This will be cleaned to satisfy ``max_backlog <= max_results``.
    """

    _max_results: Optional[int] = 10
    _timeout: Optional[int] = 30
    _max_backlog: int = 1000

    @staticmethod
    def _basic_clean(key, value) -> Optional[int]:
        """Return `value` if passes basic validity checks, else return class default.

        Validity check: `value` must be either a positive integer or None.
        """
        default = init_defaults(FlowConfigs)[key]

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
        """Maximum number of messages to pull and process before stopping."""
        self._max_results = FlowConfigs._basic_clean("max_results", self._max_results)
        return self._max_results

    @max_results.setter
    def max_results(self, value):
        self._max_results = value

    @max_results.deleter
    def max_results(self):
        self._max_results = init_defaults(self)["max_results"]

    # timeout
    @property
    def timeout(self) -> Optional[int]:
        """Maximum number of seconds to wait for a new message before stopping."""
        return FlowConfigs._basic_clean("timeout", self._timeout)

    @timeout.setter
    def timeout(self, value):
        self._timeout = value

    @timeout.deleter
    def timeout(self):
        self._timeout = init_defaults(self)["timeout"]

    # max_backlog
    @property
    def max_backlog(self) -> int:
        """Maximum number of pulled but unprocessed messages before pausing the pull."""
        max_backlog = FlowConfigs._basic_clean("max_backlog", self._max_backlog)

        # check specific validity conditions. upon failure, fall back to default value
        default = init_defaults(self)["max_backlog"]

        # max_backlog cannot be None
        if max_backlog is None:
            LOGGER.warning(f"max_backlog cannot be None. Using the default {default}.")
            max_backlog = default

        # be conservative, ensure max_backlog <= max_results
        try:
            assert max_backlog <= self.max_results

        except AssertionError:
            LOGGER.debug(
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
        self._max_backlog = init_defaults(self)["max_backlog"]


@dataclasses.dataclass
class ConsumerSettings:
    """Settings for a :class:`Consumer`.

    Parameters:
        client:
            Either a :class:`SubscriberClient` or the :class:`~pittgoogle.auth.Auth`
            or :class:`~pittgoogle.auth.AuthSettings` necessary to create one.

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


@attrs.define
class _Helpers:
    @staticmethod
    def client_from_auth(value):
        if isinstance(value, SubscriberClient):
            return value
        elif isinstance(value, Auth):
            return SubscriberClient(auth=value)

    # @staticmethod
    # def each_element_in_alert_attrs(inst, attribute, elements):
    #     alert_attrs = attrs.asdict(Alert()).keys()
    #     for element in elements:
    #         if element not in alert_attrs:
    #             raise ValueError(
    #                 f"Only attribute names of Alert are allowed in {attribute.name}."
    #             )

    @staticmethod
    def backlog_le_results(inst, attribute, value):
        """Enforce max_backlog <= max_results."""
        if attribute.name == "max_results":
            returnval = value

        if (inst.max_results is not None) and (inst.max_backlog > inst.max_results):
            LOGGER.debug(
                (
                    "Setting max_backlog = max_results to prevent an excessive number "
                    "of pulled messages that will never be processed. "
                )
            )
            inst.max_backlog = inst.max_results


@attrs.define
class Consumer:
    """Consumer class to pull a Pub/Sub subscription and process messages.

    Initialization does the following:

    #.  Unpack each element of `settings` into a property of `self`.

    #.  Authenticate the client by requesting credentials
        (``self.client.auth.credentials``).

    #.  Make sure the subscription exists in Pub/Sub (creating it, if necessary), and
        that the client can connect (``self.subscription.touch()``).

    Parameters
    -----------
    client : `SubscriberClient` or `Auth`
        Either a client or the auth information necessary to create one.
    subscription : `Subscription` or `str`
        Pub/Sub subscription to be pulled. Note that if you pass a `Subscription`, it's
        `client` will be replaced with this consumer's `client` attribute.
    flow_configs : `FlowConfigs`
        Stopping conditions and flow control settings for the streaming pull.
    callback_settings : `CallbackSettings`
        Settings for the :ref:`callbacks <callbacks>`.
        These dictate the message delivery format, processing logic, and data
        returned.

    Settings for the :ref:`callbacks <callbacks>`.

    Parameters
    ----------
    max_results : optional, `int`
        Maximum number of messages to pull and process before stopping.
        Default = 10, use None for no limit.
    timeout : optional, `int`
        Maximum number of seconds to wait for a new message before stopping.
        Default = 30. Use None for no limit.
    max_backlog : optional, `int`
        Maximum number of pulled but unprocessed messages before pausing the pull.
        Default = min(1000, ``max_results``).
        This will be cleaned to satisfy ``max_backlog <= max_results``.
    user_callback : callable
        A function, supplied by the user, that accepts a single
        :class:`pittgoogle.types.Alert` as
        its sole argument and returns a :class:`pittgoogle.types.Response`.
        The function is allowed to accept arbitrary keyword arguments, but their
        values must be passed to the consumer via the `user_kwargs` setting prior
        to starting the pull.
        See :ref:`user callback <user callback>` for more information.
    user_kwargs : `dict`
        A dictionary of key/value pairs that will be sent as kwargs to the
        ``user_callback`` by the consumer.
    unpack : iterable of `str`
        :class:`~pittgoogle.types.Alert` attributes that should be populated with data.
        This determines which data is available to the user callback.
    """

    # client: SubscriberClient  # = attrs.field()
    # subscription: Subscription  # = attrs.field(factory=Subscription)
    # flow_configs: FlowConfigs  # = attrs.field(factory=FlowConfigs)
    # callback_settings: CallbackSettings  # = attrs.field(factory=CallbackSettings)
    client: SubscriberClient = attrs.field(
        # default=attrs.Factory(SubscriberClient, takes_self=False),
        factory=SubscriberClient,
        converter=SubscriberClient,
    )
    """:class:`SubscriberClient` for the consumer."""
    subscription: Subscription = attrs.field(
        # default=attrs.Factory(Subscription, takes_self=False),
        factory=Subscription,
        converter=Subscription,
    )
    """:class:`Subscription` that the consumer will pull."""
    flow_configs: FlowConfigs = attrs.field(
        # default=attrs.Factory(FlowConfigs, takes_self=False)
        factory=FlowConfigs,
    )
    """:class:`FlowConfigs`"""
    # callback_settings: CallbackSettings = attrs.field(
    #     # default=attrs.Factory(CallbackSettings, takes_self=False)
    #     factory=CallbackSettings,
    # )
    # """:class:`CallbackSettings`"""
    user_callback: Optional[Callable[[Alert], Response]] = attrs.field(
        default=None, validator=attrs.validators.optional(attrs.validators.is_callable)
    )
    """A :ref:`user callback <user callback>` or None."""
    user_kwargs: Mapping = attrs.field(factory=dict)
    """Keyword arguments for `user_callback`."""
    unpack: Iterable[str] = attrs.field(
        default=["dict", "metadata"],
        # validator=_Helpers.each_element_in_alert_attrs,
        validator=attrs.validators.deep_iterable(
            attrs.validators.in_(attrs.asdict(Alert()).keys())
        ),
    )
    """:class:`~pittgoogle.types.Alert` attributes that will be populated with data."""
    max_results: int = attrs.field(
        default=10,
        validator=attrs.validators.optional(attrs.validators.gt(0)),
        on_setattr=_Helpers.backlog_le_results,
    )
    """Maximum number of messages to pull and process before stopping."""
    timeout: int = attrs.field(
        default=30, validator=attrs.validators.optional(attrs.validators.gt(0))
    )
    """Maximum number of seconds to wait for a new message before stopping."""
    max_backlog: int = attrs.field(default=1000, on_setattr=_Helpers.backlog_le_results)
    """Maximum number of pulled but unprocessed messages before pausing the pull."""

    def __attrs_post_init__(self):
        """Force the `subscription` to use `self.client`."""
        self.subscription.client = self.client

    # custom init so that we can accept **kwargs
    def __init__(
        self,
        **kwargs,
    ):
        def _kwargs_then_attrs(kwargs, obj):
            init_varnames = inspect.signature(obj.__init__).parameters.keys()
            # field_names = [field.name for field in dataclasses.fields(obj)]
            return dict((k, kwargs.get(k, getattr(obj, k))) for k in init_varnames)

        # create client
        myattrs = dict(
            client=SubscriberClient(
                **_kwargs_then_attrs(kwargs, kwargs.get("client", SubscriberClient()))
            )
        )

        # the subscription should use this same client
        kwargs["client"] = attrs["client"]

        # create other attributes
        for attr, factory in (
            ("subscription", Subscription),
            ("flow_configs", FlowConfigs),
            ("callback_settings", CallbackSettings),
        ):
            myattrs[attr] = factory(
                **_kwargs_then_attrs(kwargs, kwargs.get(attr, factory()))
            )
        # subscription = Subscription(
        #     **_kwargs_then_attrs(kwargs, kwargs.get("subscription", Subscription()))
        # )
        # flow_configs = FlowConfigs(
        #     **_kwargs_then_attrs(kwargs, kwargs.get("flow_configs", FlowConfigs()))
        # )
        # callback_settings = CallbackSettings(
        #     **_kwargs_then_attrs(
        #         kwargs, kwargs.get("callback_settings", CallbackSettings())
        #     )
        # )
        self.__attrs_init__(**attrs)
        # subscription = Subscription(kwargs.pop("subscription", None))
        # flow_configs = kwargs.pop("flow_configs", FlowConfigs())
        # callback_settings = kwargs.pop("callback_settings", CallbackSettings())
        #
        # self.__attrs_init__(
        #     client=client,
        #     subscription=Subscription(
        #         **_kwargs_then_attrs(
        #             dict(**kwargs, client=client), Subscription(subscription)
        #         )
        #     ),
        #     flow_configs=FlowConfigs(**_kwargs_then_attrs(kwargs, flow_configs)),
        #     callback_settings=CallbackSettings(
        #         **_kwargs_then_attrs(kwargs, callback_settings)
        #     ),
        # )

        # # authenticate and store credentials
        # self.client.auth.credentials
        # self.projectid = self.client.auth.GOOGLE_CLOUD_PROJECT
        #
        # # check connection to the subscription
        # if self.subscription._client is None:
        #     self.subscription._client = self._client
        # self.subscription.touch()
        #
        # # list of results of user processing. stored and returned upon user request
        # self._results = None
        #
        # # instantiate a queue to communicate with the background thread
        # self.__queue = None

    # subscriber client
    # @property
    # def client(self) -> Optional[SubscriberClient]:
    #     """:class:`SubscriberClient` for the consumer.
    #
    #     If this is set to a :class:`pittgoogle.auth.Auth` or
    #     :class:`pittgoogle.auth.AuthSettings` it will be used to
    #     instantiate a :class:`SubscriberClient`, which will then replace it.
    #     """
    #     if self._client is None:
    #         # nothing to do but warn
    #         LOGGER.warning("Cannot create a SubscriberClient.")
    #
    #     else:
    #         # make sure we have a SubscriberClient and not just an Auth or AuthSettings
    #         self._client = SubscriberClient(self._client)
    #
    #     return self._client
    #
    # @client.setter
    # def client(self, value):
    #     # make sure we have a SubscriberClient and not just an Auth or AuthSettings
    #     self._client = SubscriberClient(value)
    #
    # @client.deleter
    # def client(self):
    #     self._client = None

    # # subscription
    # @property
    # def subscription(self) -> Subscription:
    #     """Subscription to be pulled.
    #
    #     If this is set to a string it will be used along with `self.client` to create a
    #     :class:`Subscription` with the default topic.
    #     If you need the subscription to be created and attached
    #     to a non-default topic, use a :class:`Subscription` directly.
    #
    #     If deleted, this is reset to None and the default subscription name is used with
    #     `self.client` to create the :class:`Subscription`.
    #     """
    #     if isinstance(self._subscription, str):
    #         self._subscription = Subscription(
    #             name=self._subscription, client=self.client
    #         )
    #
    #     elif self._subscription is None:
    #         self._subscription = Subscription(client=self.client)
    #
    #     return self._subscription
    #
    # @subscription.setter
    # def subscription(self, value):
    #     self._subscription = value
    #
    # @subscription.deleter
    # def subscription(self):
    # self._subscription = None

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

                If False, this method returns immediately after opening the stream.
                Use this option with caution.
                The pull will continue in the background, but the consumer will not
                automatically control the flow (e.g., it will not enforce the stopping
                conditions).
                Thus the pull can run in the background indefinitely.
                You can stop it manually by calling :meth:`Consumer().stop()`.

                If block=False gives the desired behavior,
                consider opening the stream by calling the Pub/Sub API directly.
                This will give you more control over the pull, including the option
                to parallelize it.
                The Pub/Sub command is documented
                `here <https://googleapis.dev/python/pubsub/latest/subscriber/api/client.html#google.cloud.pubsub_v1.subscriber.client.Client.subscribe>`__.
                It can be executed using the consumer's client:

                .. code-block:: python

                    from pittgoogle import pubsub

                    consumer = pubsub.Consumer(pubsub.ConsumerSettings())
                    consumer.streaming_pull_future = consumer.client.client.subscribe()

                (also send appropriate args/kwargs).
                Assigning the result to ``consumer.streaming_pull_future``
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
        self.streaming_pull_future = self.client.client.subscribe(
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
        except (KeyboardInterrupt, Exception):
            self.stop()
            raise

        LOGGER.debug(
            (
                f"Processed {total_count} messages from {self.subscription.path}. "
                "The actual number of messages that were pulled and acknowledged "
                "may be higher if the user elected not to count some messages "
                "(e.g., by returning Response(result='filter_out') from the "
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
            response = self._execute_user_callback(alert)

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

        def _my_bytes(message):
            """Return the message payload without changing the format."""
            LOGGER.debug("Alert bytes requested. Extracting.")
            return message.data

        def _my_dict(message):
            LOGGER.debug("Alert dict requested. Unpacking.")
            """Return the message payload as a dictionary."""
            return Cast.avro_to_dict(message.data)

        def _my_metadata(message):
            """Return the message metadata and custom attributes as a dictionary."""
            LOGGER.debug("Alert metadata requested. Unpacking.")
            return {
                "message_id": message.message_id,
                "publish_time": message.publish_time,
                # ordering must be enabled on the subscription for this to be useful
                "ordering_key": message.ordering_key,
                **dict((k, v) for k, v in message.attributes.items()),
            }

        def _my_msg(message):
            """Return the original Pub/Sub message object."""
            LOGGER.debug("Alert msg requested. Returning message.")
            return message

        # return an Alert, saving only what's requested in callback_settings.unpack
        LOGGER.debug(
            (
                "Unpacking the message into a pittgoogle.types.Alert. "
                f"Populating attributes {self.callback_settings.unpack}"
            )
        )

        unpack_fncs = dict(
            bytes=_my_bytes,
            dict=_my_dict,
            metadata=_my_metadata,
            msg=_my_msg,
        )

        def _my_unpack(self, key, message):
            """Unpack the data if `key` in `self.callback_settings.unpack`."""
            if key in self.callback_settings.unpack:
                if key == "metadata":
                    print(unpack_fncs.get(key)(message))
                return unpack_fncs.get(key)(message)
            else:
                LOGGER.debug(f"Alert.{key} not requested. Populating with None.")

        return Alert._make(_my_unpack(self, k, message) for k in Alert._fields)

    def _execute_user_callback(self, alert: Alert) -> Response:
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
        """:ref:`user callback <user callback>` example that simply requests that the alert be collected.

        Returns:
            ``Response(ack=True, result=alert)``

        Use this as the :attr:`~CallbackSettings.user_callback` if you want the alerts
        stored in the consumer's :attr:`~Consumer.results` attribute for later access.

        consumer.callback_settings.user_callback = Consumer.collect_alert
        """
        return Response(ack=True, result=alert)

    @property
    def results(self):
        """Container to store results returned from a :ref:`user callback <user callback>`."""
        if self._results is None:
            self._results = list()
        return self._results

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
