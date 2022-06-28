#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""pittgoogle types.

.. contents:: Classes
   :local:
   :depth: 1

`Alert`
--------

.. autoclass:: Alert
   :members:
   :member-order: bysource

`Response`
----------

.. autoclass:: Response
   :members:
   :member-order: bysource

`PittGoogleProjectIds`
------------------------

.. autoclass:: PittGoogleProjectIds
   :members:
   :member-order: bysource
"""

from dataclasses import dataclass
from typing import Any, ByteString, ClassVar, Dict, NamedTuple, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from google.cloud import pubsub_v1


class Alert(NamedTuple):
    """Container for an alert.

    A Pub/Sub message is of type: `google.cloud.pubsub_v1.types.PubsubMessage`, which is
    documented `here <https://googleapis.dev/python/pubsub/latest/types.html>`__.

    The pittgoogle client will unpack the message into this container and deliver it to
    the user (e.g., to a :ref:`user callback`).
    The attributes will be populated according to the request.

    Attributes:
        bytes:
            Message payload (i.e., alert packet data) in its original format --
            Avro or JSON serialized bytes.
        dict:
            Message payload unpacked into a dictionary.
        metadata:
            The message metadata and Pitt-Google's custom attributes.
            These include, for example, the message `publish_time` and the alert's
            `sourceId`.
        msg:
            The Pub/Sub message object.
    """

    dict: Optional[Dict] = None
    bytes: Optional[ByteString] = None
    metadata: Optional[Dict] = None
    msg: Optional["pubsub_v1.types.PubsubMessage"] = None


class Response(NamedTuple):
    """Container for a response, to be returned by a user_callback.

    (see :class:`pittgoogle.pubsub.Consumer`)

    Attributes:
        ack:
            Whether to acknowledge the message. In general, this should be True if the
            message was processed successfully, and False if an error was encountered.
            See :ref:`ack and nack` for more information.

        result:
            Any object the user wishes to return after processing the alert.
            This will be handled by a :class:`~pittgoogle.pubsub.Consumer` as follows:

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
class PittGoogleProjectIds:
    """Pitt-Google broker's Google Cloud project IDs."""

    production: ClassVar[str] = "ardent-cycling-243415"
    testing: ClassVar[str] = "avid-heading-329016"
    billing: ClassVar[str] = "light-cycle-328823"
