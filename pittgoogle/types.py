#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""pittgoogle types."""

from typing import TYPE_CHECKING, Any, ByteString, Dict, Optional

import attrs

if TYPE_CHECKING:
    from google.cloud import pubsub_v1


@attrs.frozen(kw_only=True)
class Alert:
    """Container for an alert.

    A Pub/Sub message is of type: `google.cloud.pubsub_v1.types.PubsubMessage`, which is
    documented `here <https://googleapis.dev/python/pubsub/latest/types.html>`__.

    The pittgoogle client will unpack the Pub/Sub message into this container and
    deliver it to the user (e.g., to a :ref:`user callback <user callback>`).
    The attributes will be populated according to the user's request.

    Parameters
    ------------
    bytes : `bytes`
        Message payload (i.e., alert packet data) in its original format --
        Avro or JSON serialized bytes.
    dict : `dict`
        Message payload (i.e., alert packet data) unpacked into a dictionary.
    metadata : `dict`
        The message metadata and Pitt-Google's custom attributes.
        These include, for example, the message `publish_time` and the alert's
        `sourceId`.
    msg : `google.cloud.pubsub_v1.types.PubsubMessage`
        The Pub/Sub message object.
    """

    bytes: Optional[ByteString] = None
    """Message payload in original format -- Avro or JSON serialized bytes."""
    dict: Optional[Dict] = None
    """Message payload unpacked into a dictionary."""
    metadata: Optional[Dict] = None
    """Message metadata and Pitt-Google's custom attributes."""
    msg: Optional["pubsub_v1.types.PubsubMessage"] = None
    """Original Pub/Sub message object."""


@attrs.frozen(kw_only=True)
class Response:
    """Container for a response, to be returned by a :ref:`user callback <user callback>`.

    Parameters
    ------------
    ack : `bool`
        Whether to acknowledge the message. In general, this should be True if the
        message was processed successfully, and False if an error was encountered.
        See :ref:`ack and nack` for more information.

    result : `Any`
        Any object the user wishes to return after processing the alert.
        This will be handled by a :class:`~pittgoogle.pubsub.Consumer` as follows:

        -   None: This is the recommended value, if the user_callback ran
            successfully. This value
            will NOT be stored in `Consumer().results`, but the message
            WILL be counted against `Consumer().flow_configs.max_results`.
            The assumption is that the user_callback saved any results that
            need to be persisted.

        -   False: This option allows the user to drop messages that do not pass a
            custom filter. This value
            will NOT be stored in `Consumer().results`, and the message
            will NOT be counted against `Consumer().flow_configs.max_results`.

        -   Any other value: WILL be stored in `Consumer().results`, and the message
            WILL be counted against `Consumer().flow_configs.max_results`.
    """

    ack: bool = True
    result: Any = None
