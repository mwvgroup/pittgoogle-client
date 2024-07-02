# -*- coding: UTF-8 -*-
"""Classes defining new types."""
import datetime
import importlib.resources
import logging

import attrs

LOGGER = logging.getLogger(__name__)
PACKAGE_DIR = importlib.resources.files(__package__)


@attrs.define(frozen=True)
class PubsubMessageLike:
    """Container for an incoming alert.

    Do not use this class directly. Use :class:`pittgoogle.alert.Alert` instead.

    Purpose:
    It is convenient for the `Alert` class to work with a message as a
    `google.cloud.pubsub_v1.types.PubsubMessage`. However, there are many ways to obtain an `Alert`
    that do not result in a `google.cloud.pubsub_v1.types.PubsubMessage` (e.g., an alert packet
    loaded from disk or an incoming message to a Cloud Functions or Cloud Run module). In those
    cases, this class is used to create an object with the same attributes as a
    `google.cloud.pubsub_v1.types.PubsubMessage`. This object is then assigned to the `msg`
    attribute of the `Alert`.

    ----
    """

    data: bytes = attrs.field()
    """Alert data as bytes. This is also known as the message "payload"."""
    attributes: dict = attrs.field(factory=dict)
    """Alert attributes. This is custom metadata attached to the Pub/Sub message."""
    message_id: str | None = attrs.field(default=None)
    """Pub/Sub ID of the published message."""
    publish_time: datetime.datetime | None = attrs.field(default=None)
    """Timestamp of the published message."""
    ordering_key: str | None = attrs.field(default=None)
    """Pub/Sub ordering key of the published message."""
