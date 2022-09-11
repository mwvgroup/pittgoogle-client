#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""pittgoogle types."""

from typing import TYPE_CHECKING, Any, ByteString, Dict, Optional

import attrs

if TYPE_CHECKING:
    from google.cloud import pubsub_v1


@attrs.frozen(kw_only=True)
class Alert:
    """Pitt-Google container for an alert delivered by Pub/Sub.

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
        The Pub/Sub message object,
        documented at `<https://googleapis.dev/python/pubsub/latest/types.html>`__.
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
    """Container for a response, to be returned by a :attr:`Consumer.user_callback`.

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
            successfully.
            This value will NOT be stored in :attr:`~Consumer.results`, but the message
            WILL be counted against :attr:`~Consumer.max_results`.
            The assumption is that the :attr:`~Consumer.user_callback`
            saved any results that it wants.

        -   False: This option allows the user to drop messages that do not pass a
            custom filter.
            This value will NOT be stored in :attr:`~Consumer.results`, and the message
            will NOT be counted against :attr:`~Consumer.max_results`.

        -   Any other value: WILL be stored in :attr:`~Consumer.results`, and the
            message WILL be counted against :attr:`~Consumer.max_results`.
    """

    ack: bool = attrs.field(default=True, converter=attrs.converters.to_bool)
    result: Any = attrs.field(default=None)
