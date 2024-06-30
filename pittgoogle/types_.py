# -*- coding: UTF-8 -*-
"""Classes defining new types."""
import datetime
import importlib.resources
import logging
from pathlib import Path
from typing import Optional

import fastavro
import yaml
from attrs import define, field

LOGGER = logging.getLogger(__name__)
PACKAGE_DIR = importlib.resources.files(__package__)


@define(kw_only=True)
class Schema:
    """Class for an individual schema.

    This class is not intended to be used directly.
    Use :class:`pittgoogle.Schemas` instead.
    """

    name: str = field()
    description: str = field()
    path: Path | None = field(default=None)
    _map: dict | None = field(default=None, init=False)
    _avsc: dict | None = field(default=None, init=False)

    @property
    def survey(self) -> str:
        """Name of the survey. This is the first block (separated by ".") in the schema's name."""
        return self.name.split(".")[0]

    @property
    def definition(self) -> str:
        """Pointer (e.g., URL) to the survey's schema definition."""
        return self.map.SURVEY_SCHEMA

    @property
    def map(self) -> dict:
        """Mapping of Pitt-Google's generic field names to survey-specific field names."""
        if self._map is None:
            yml = PACKAGE_DIR / f"schemas/maps/{self.survey}.yml"
            try:
                self._map = yaml.safe_load(yml.read_text())
            except FileNotFoundError:
                raise ValueError(f"no schema map found for schema name '{self.name}'")
        return self._map

    @property
    def avsc(self) -> Optional[dict]:
        """The Avro schema loaded from the file at `self.path`, or None if a valid file cannot be found."""
        # if the schema has already been loaded, return it
        if self._avsc is not None:
            return self._avsc

        # if self.path does not point to an existing avro schema file, return None
        if (self.path is None) or (self.path.suffix != ".avsc") or (not self.path.is_file()):
            return None

        # load the schema and return it
        self._avsc = fastavro.schema.load_schema(self.path)
        return self._avsc


@define(frozen=True)
class PubsubMessageLike:
    """Container for an incoming alert.

    It is convenient for the :class:`pittgoogle.Alert` class to work with a message as a
    `pubsub_v1.types.PubsubMessage`. However, there are many ways to obtain an alert that do
    not result in a `pubsub_v1.types.PubsubMessage` (e.g., an alert packet loaded from disk or
    an incoming message to a Cloud Functions or Cloud Run module). In those cases, this class
    is used to create an object with the same attributes as a `pubsub_v1.types.PubsubMessage`.
    This object is then assigned to the `msg` attribute of the `Alert`.
    """

    data: bytes = field()
    """Alert data as bytes. This is also known as the message "payload"."""
    attributes: dict = field(factory=dict)
    """Alert attributes. This is custom metadata attached to the Pub/Sub message."""
    message_id: str | None = field(default=None)
    """Pub/Sub ID of the published message."""
    publish_time: datetime.datetime | None = field(default=None)
    """Timestamp of the published message."""
    ordering_key: str | None = field(default=None)
    """Pub/Sub ordering key of the published message."""
