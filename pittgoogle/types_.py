# -*- coding: UTF-8 -*-
"""Functions to support working with alerts and related data."""
import importlib.resources
import logging
from typing import TYPE_CHECKING, Optional

import fastavro
import yaml
from attrs import define, field

if TYPE_CHECKING:
    import datetime
    from pathlib import Path

LOGGER = logging.getLogger(__name__)
PACKAGE_DIR = importlib.resources.files(__package__)


@define(kw_only=True)
class Schema:
    """Class for an individual schema.

    This class is not intended to be used directly. Instead, get a schema from the registry:
    `pittgoogle.registry.Schemas`.
    """

    name: str = field()
    description: str = field()
    path: Optional["Path"] = field(default=None)
    _map: Optional[dict] = field(default=None, init=False)
    _avsc: Optional[dict] = field(default=None, init=False)

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
    """Container for an incoming Pub/Sub message that mimics a `google.cloud.pubsub_v1.types.PubsubMessage`.

    It is convenient for the :class:`pittgoogle.Alert` class to work with a message as a
    `pubsub_v1.types.PubsubMessage`. However, there are many ways to obtain an alert that do
    not result in a `pubsub_v1.types.PubsubMessage` (e.g., an alert packet loaded from disk or
    an incoming message to a Cloud Functions or Cloud Run module). In those cases, this class
    is used to create an object with the same attributes as a `pubsub_v1.types.PubsubMessage`.
    This object is then assigned to the `msg` attribute of the `Alert`.
    """

    data: bytes = field()
    attributes: dict = field(factory=dict)
    message_id: Optional[str] = field(default=None)
    publish_time: Optional["datetime.datetime"] = field(default=None)
    ordering_key: Optional[str] = field(default=None)
