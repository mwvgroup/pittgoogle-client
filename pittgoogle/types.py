#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""pittgoogle types."""

import attrs
from dataclasses import dataclass
from typing import Any, ByteString, ClassVar, Dict, NamedTuple, Optional, TYPE_CHECKING
from base64 import b64decode, b64encode
import fastavro
from io import BytesIO
import json
from astropy.time import Time


if TYPE_CHECKING:
    from google.cloud import pubsub_v1


@attrs.frozen(kw_only=True)
class Alert:
    """Container for an alert.

    A Pub/Sub message is of type: `google.cloud.pubsub_v1.types.PubsubMessage`, which is
    documented `here <https://googleapis.dev/python/pubsub/latest/types.html>`__.

    The pittgoogle client will unpack the Pub/Sub message into this container and
    deliver it to the user (e.g., to a :ref:`user callback`).
    The attributes will be populated according to the user's request.

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


@attrs.frozen(kw_only=True)
class Response:
    """Container for a response, to be returned by a :ref:`user callback`.

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


@dataclass
class Cast:
    """Methods to convert data types."""

    @staticmethod
    def bytes_to_b64utf8(bytes_data):
        """Convert bytes data to UTF8.

        Args:
            bytes_data (bytes): Bytes data

        Returns:
            A string in UTF-8 format
        """
        if bytes_data is not None:
            return b64encode(bytes_data).decode("utf-8")

    @staticmethod
    def base64_to_dict(bytes_data):
        """Convert base64 encoded bytes data to a dict.

        Args:
            bytes_data (base64 bytes): base64 encoded bytes

        Returns:
            A dictionary
        """
        if bytes_data is not None:
            return json.loads(b64decode(bytes_data).decode("utf-8"))

    @staticmethod
    def avro_to_dict(bytes_data):
        """Convert Avro serialized bytes data to a dict.

        Args:
            bytes_data (bytes): Avro serialized bytes

        Returns:
            A dictionary
        """
        if bytes_data is not None:
            with BytesIO(bytes_data) as fin:
                alert_dicts = [r for r in fastavro.reader(fin)]  # list with single dict
            return alert_dicts[0]

    @staticmethod
    def b64avro_to_dict(bytes_data):
        """Convert base64 encoded, Avro serialized bytes data to a dict.

        Args:
            bytes_data (bytes): base64 encoded, Avro serialized bytes

        Returns:
            A dictionary
        """
        return Cast.avro_to_dict(b64decode(bytes_data))
        # if bytes_data is not None:
        #     with BytesIO(b64decode(bytes_data)) as fin:
        #         alert_dicts = [r for r in fastavro.reader(fin)]  # list with single dict
        #     return alert_dicts[0]

    @staticmethod
    def jd_to_readable_date(jd):
        """Convert a julian date to a human readable string.

        Args:
            jd (float): Datetime value in julian format

        Returns:
            String in 'day mon year hour:min' format
        """
        return Time(jd, format="jd").strftime("%d %b %Y - %H:%M:%S")
