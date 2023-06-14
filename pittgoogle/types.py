#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""pittgoogle types."""

from typing import TYPE_CHECKING, Any, ByteString, Dict, Optional

import attrs
from .utils import Cast

if TYPE_CHECKING:
    from google.cloud import pubsub_v1


@attrs.define(kw_only=True)
class Alert:
    """Pitt-Google container for an alert delivered by Pub/Sub.

    Parameters
    ------------
    bytes : `bytes`
        Alert packet as a byte string. It may be Avro or JSON serialized depending on the topic.
    dict : `dict`
        Alert packet as a dictionary.
    metadata : `dict`
        Pub/Sub metadata.
    msg : `google.cloud.pubsub_v1.types.PubsubMessage`
        The Pub/Sub message object,
        documented at `<https://googleapis.dev/python/pubsub/latest/types.html>`__.
    """

    _bytes: Optional[ByteString] = attrs.field(default=None)
    """Message payload in original format -- Avro or JSON serialized bytes."""
    _dict: Optional[Dict] = attrs.field(default=None)
    """Message payload unpacked into a dictionary."""
    _metadata: Optional[Dict] = attrs.field(default=None)
    """Message metadata and Pitt-Google's custom attributes."""
    msg: Optional["pubsub_v1.types.PubsubMessage"] = attrs.field(default=None)
    """Original Pub/Sub message object."""

    @property
    def bytes(self):
        """."""
        if self._bytes is None:
            # add try-except when we know what we're looking for
            self._bytes = self.msg.data
            if self._bytes is None:
                with open(self.path, "rb") as f:
                    self._bytes = f.read()
        return self._bytes

    @property
    def dict(self):
        """."""
        if self._dict is None:
            # add try-except when we know what we're looking for
            self._dict = Cast.avro_to_dict(self.bytes)
            if self._dict is None:
                self._dict = Cast.json_to_dict(self.bytes)
        return self._dict

    @property
    def metadata(self):
        """Return the message metadata and custom attributes as a dictionary."""
        if self._metadata is None:
            self._metadata = {
                "message_id": self.msg.message_id,
                "publish_time": self.msg.publish_time,
                # ordering must be enabled on the subscription for this to be useful
                "ordering_key": self.msg.ordering_key,
                # flatten the dict containing our custom attributes
                **self.msg.attributes,
                # **dict((k, v) for k, v in self.msg.attributes.items()),
            }
        return self._metadata


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

    @property
    def _count(self) -> int:
        """Return the number of times this result should be counted towards a total.

        Returns 0 if ``self.result`` is ``False``, else 1.
        """
        if isinstance(self.result, bool) and not self.result:  # self.result == False
            return 0
        return 1

    @property
    def _store(self) -> bool:
        """Whether ``self.result`` should be stored for later processing.

        Returns False if ``self._count`` == 0 or ``self.result`` is ``None``, else True.
        """
        if self._count == 0 or self.result is None:
            return False
        return True
