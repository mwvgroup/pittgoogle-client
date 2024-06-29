# -*- coding: UTF-8 -*-
"""Classes defining new types."""
import datetime
import importlib.resources
import logging
from pathlib import Path

import fastavro
import yaml
from attrs import define, field

LOGGER = logging.getLogger(__name__)
PACKAGE_DIR = importlib.resources.files(__package__)


@define(kw_only=True)
class Schema:
    """Class for an individual schema.

    This class is not intended to be used directly. Use :class:`pittgoogle.Schemas` instead.
    """

    """The name of the schema."""
    name: str = field()
    """The description of the schema."""
    description: str = field()
    """Name of the `Schema` helper method used to load the schema."""
    _helper: str = field(default="_local_avsc_helper")
    """Path where the helper can find the schema."""
    path: Path | None = field(default=None)
    """Mapping of Pitt-Google's generic field names to survey-specific field names."""
    _map: dict | None = field(default=None, init=False)
    """The Avro schema loaded by the helper or None if no Avro schema exists."""
    avsc: dict | None = field(default=None, init=False)

    @classmethod
    def from_yaml(cls, schema_dict: dict) -> "Schema":
        # initialize the class, then let the helper finish up
        schema = cls(**schema_dict)
        helper = getattr(cls, schema._helper)
        schema = helper(schema)
        return schema

    @staticmethod
    def _local_avsc_helper(schema: "Schema") -> "Schema":
        """Resolve `schema.path`. If it points to a valid ".avsc" file, load it into `schema.avsc`."""
        # Resolve the path. If it is not None, this helper expects it to be the path to
        # a ".avsc" file relative to the pittgoogle package directory.
        schema.path = PACKAGE_DIR / schema.path if schema.path is not None else None

        # Load the avro schema, if the file exists.
        invalid_path = (
            (schema.path is None) or (schema.path.suffix != ".avsc") or (not schema.path.is_file())
        )
        if invalid_path:
            schema.avsc = None
        else:
            schema.avsc = fastavro.schema.load_schema(schema.path)

        return schema

    @staticmethod
    def _lsst_avsc_helper(schema: "Schema") -> "Schema":
        """Resolve `schema.path`. If it points to a valid ".avsc" file, load the Avro schema."""
        import lsst.alert.packet.schema

        major, minor = schema.path.split(".")  # [FIXME]
        schema.path = lsst.alert.packet.schema.get_schema_path(major, minor)
        schema.avsc = lsst.alert.packet.schema.Schema.from_file(schema.path)

        return schema

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

    # @property
    # def avsc(self) -> Optional[dict]:
    #     """The Avro schema loaded from the file at `self.path`, or None if a valid file cannot be found."""
    #     # if the schema has already been loaded, return it
    #     if self._avsc is not None:
    #         return self._avsc

    #     # if self.path does not point to an existing avro schema file, return None
    #     if (self.path is None) or (self.path.suffix != ".avsc") or (not self.path.is_file()):
    #         return None

    #     # load the schema and return it
    #     self._avsc = fastavro.schema.load_schema(self.path)
    #     return self._avsc


@define(frozen=True)
class PubsubMessageLike:
    """Container for an incoming alert.

    This class is not intended to be used directly.
    Use :class:`pittgoogle.Alert` instead.

    Purpose:
    It is convenient for the :class:`pittgoogle.Alert` class to work with a message as a
    `google.cloud.pubsub_v1.types.PubsubMessage`. However, there are many ways to obtain an alert
    that do not result in a `google.cloud.pubsub_v1.types.PubsubMessage` (e.g., an alert packet
    loaded from disk or an incoming message to a Cloud Functions or Cloud Run module). In those
    cases, this class is used to create an object with the same attributes as a
    `google.cloud.pubsub_v1.types.PubsubMessage`. This object is then assigned to the `msg`
    attribute of the `Alert`.
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
