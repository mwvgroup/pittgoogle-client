# -*- coding: UTF-8 -*-
"""Classes to manage alert schemas."""
import importlib.resources
import io
import json
import logging
import re
from pathlib import Path

import attrs
import fastavro
import yaml

from . import exceptions, utils

LOGGER = logging.getLogger(__name__)
PACKAGE_DIR = importlib.resources.files(__package__)


@attrs.define(kw_only=True)
class SchemaHelpers:
    """Class to organize helper functions.

    This class is not intended to be used directly, except by developers adding support for a new schema.

    For Developers:

        When a user requests a schema from the registry, the class method :meth:`Schema._from_yaml` is called.
        The method will pass ``schema_name``'s dict entry from the registry's `schemas.yml` file to
        one of these helper methods, which will then construct the :class:`Schema` object.

        If you are adding support for a new schema, you will need to point to the appropriate helper
        method for your schema using the ``helper`` field in the registry's `schemas.yml` file.
        If an appropriate method does not exist in this class, you will need to add one.

    ----
    """

    @staticmethod
    def default_schema_helper(schema_dict: dict) -> "Schema":
        """Resolve `schema.path`. If it points to a valid ".avsc" file, load it into `schema.avsc`."""
        schema = _DefaultSchema(**schema_dict)

        # Resolve the path. If it is not None, this helper expects it to be the path to
        # a ".avsc" file relative to the pittgoogle package directory.
        schema.path = PACKAGE_DIR / schema.path if schema.path is not None else None

        # Load the avro schema, if the file exists. Fallback to None.
        invalid_path = (
            (schema.path is None) or (schema.path.suffix != ".avsc") or (not schema.path.is_file())
        )
        if invalid_path:
            schema.definition = None
        else:
            schema.definition = fastavro.schema.load_schema(schema.path)

        return schema

    @staticmethod
    def elasticc_schema_helper(schema_dict: dict) -> "Schema":
        schema = _SchemalessAvroSchema(**schema_dict)

        # Resolve the path and load the schema
        schema.path = PACKAGE_DIR / schema.path
        schema.definition = fastavro.schema.load_schema(schema.path)

        return schema

    @staticmethod
    def lsst_schema_helper(schema_dict: dict) -> "Schema":
        """Load the Avro schema definition for lsst.v7_1.alert.

        [FIXME] This is hack to get the latest schema version into pittgoogle-client
        until we can get :meth:`SchemaHelpers.lsst_auto_schema_helper` working.
        """
        if not schema_dict["name"] == "lsst.v7_1.alert":
            raise NotImplementedError("Only 'lsst.v7_1.alert' is supported for LSST.")

        schema = _ConfluentWireAvroSchema(**schema_dict)

        # Resolve the path and load the schema
        schema.path = PACKAGE_DIR / schema.path
        schema.definition = fastavro.schema.load_schema(schema.path)

        return schema

    @staticmethod
    def lsst_auto_schema_helper(schema_dict: dict) -> "Schema":
        """Load the Avro schema definition using the ``lsst.alert.packet`` package.

        Raises:
            SchemaError:
                If an LSST schema called ``schema.name`` cannot be loaded. An error is raised
                because the LSST alert bytes are schemaless, so ``schema.definition`` will be
                required in order to deserialize the alert.
        """
        import lsst.alert.packet.schema

        schema = _ConfluentWireAvroSchema(**schema_dict)

        version_msg = f"For valid versions, see {schema.origin}."

        # Parse major and minor versions out of schema.name. Expecting syntax "lsst.v<MAJOR>_<MINOR>.alert".
        try:
            major, minor = map(int, re.findall(r"\d+", schema.name))
        except ValueError:
            msg = (
                f"Unable to identify major and minor version. Please use the syntax "
                "'lsst.v<MAJOR>_<MINOR>.alert', replacing '<MAJOR>' and '<MINOR>' with integers. "
                f"{version_msg}"
            )
            raise exceptions.SchemaError(msg)

        schema_dir = Path(lsst.alert.packet.schema.get_schema_path(major, minor))
        schema.path = schema_dir / f"{schema.name}.avsc"

        try:
            schema.definition = lsst.alert.packet.schema.Schema.from_file(schema.path).definition
        except fastavro.repository.SchemaRepositoryError:
            msg = f"Unable to load the schema. {version_msg}"
            raise exceptions.SchemaError(msg)

        return schema


@attrs.define(kw_only=True)
class Schema:
    """Class for an individual schema.

    Do not call this class's constructor directly. Instead, load a schema using the registry
    :class:`pittgoogle.registry.Schemas`.

    ----
    """

    # String _under_ field definition will cause field to appear as a property in rendered docs.
    name: str = attrs.field()
    """Name of the schema."""
    description: str = attrs.field()
    """A description of the schema."""
    origin: str = attrs.field()
    """Pointer to the schema's origin. Typically this is a URL to a repo maintained by the survey."""
    definition: dict | None = attrs.field(default=None)
    """The schema definition used to serialize and deserialize the alert bytes, if one is required."""
    _helper: str = attrs.field(default="default_schema_helper")
    """Name of the method in :class:`SchemaHelpers` used to load this schema."""
    path: Path | None = attrs.field(default=None)
    """Path where the helper can find the schema, if needed."""
    filter_map: dict = attrs.field(factory=dict)
    """Mapping of the filter name as stored in the alert (often an int) to the common name (often a string)."""
    # The rest don't need string descriptions because we will define them as explicit properties.
    _survey: str | None = attrs.field(default=None)
    # _map is important, but don't accept it as an init arg. We'll load it from a yaml file later.
    _map: dict | None = attrs.field(default=None, init=False)

    @classmethod
    def _from_yaml(cls, schema_dict: dict, **schema_dict_replacements) -> "Schema":
        """Create a :class:`Schema` object from an entry in the registry's `schemas.yml` file.

        This method calls a helper method in :class:`SchemaHelpers` to finish the initialization.

        Args:
            schema_dict (dict):
                A dictionary containing the schema information.
            **schema_dict_replacements:
                Additional keyword arguments that will override entries in ``schema_dict``.

        Returns:
            Schema:
                The created `Schema` object.
        """
        # Combine the args and kwargs then let the helper finish up the initialization.
        my_schema_dict = schema_dict.copy()
        my_schema_dict.update(schema_dict_replacements)
        helper = getattr(SchemaHelpers, my_schema_dict["helper"])
        return helper(my_schema_dict)

    @property
    def survey(self) -> str:
        """Name of the survey. This is usually the first part of the schema's name."""
        if self._survey is None:
            self._survey = self.name.split(".")[0]
        return self._survey

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


class _DefaultSchema(Schema):
    """Default schema to serialize and deserialize alert bytes."""

    def serialize(self, alert_dict: dict) -> bytes:
        """Serialize `alert_dict` using the JSON format.

        Args:
            alert_dict (dict):
                The dictionary to be serialized.

        Returns:
            bytes:
                The serialized data in bytes.
        """
        return json.dumps(alert_dict).encode("utf-8")

    def deserialize(self, alert_bytes: bytes) -> dict:
        """Deserialize `alert_bytes`.

        Args:
            alert_bytes (bytes):
                The bytes to be deserialized. This is expected to be serialized as either
                Avro with the schema attached in the header or JSON.

        Returns:
            A dictionary representing the deserialized ``alert_bytes``.

        Raises:
            SchemaError:
                If the deserialization fails after trying both JSON and Avro.
        """
        # [FIXME] This should be redesigned.
        # For now, just try avro then json, catching basically all errors in the process.
        try:
            return utils.Cast.avro_to_dict(alert_bytes)
        except Exception:
            try:
                return utils.Cast.json_to_dict(alert_bytes)
            except Exception:
                raise exceptions.SchemaError("Failed to deserialize the alert bytes")


class _SchemalessAvroSchema(Schema):
    """Schema to serialize and deserialize alert bytes in the schemaless Avro format."""

    def serialize(self, alert_dict: dict) -> bytes:
        """Serialize `alert_dict` using the schemaless Avro format."""
        fout = io.BytesIO()
        fastavro.schemaless_writer(fout, self.definition, alert_dict)
        fout.seek(0)
        message = fout.getvalue()
        return message

    def deserialize(self, alert_bytes: bytes) -> dict:
        bytes_io = io.BytesIO(alert_bytes)
        return fastavro.schemaless_reader(bytes_io, self.definition)  # [FIXME]


class _ConfluentWireAvroSchema(Schema):
    """Schema to serialize and deserialize alert bytes in the Avro Confluent Wire Format."""

    def serialize(self, alert_dict: dict) -> bytes:
        raise NotImplementedError("Confluent Wire Format not yet supported.")

    def deserialize(self, alert_bytes: bytes) -> dict:
        bytes_io = io.BytesIO(alert_bytes[5:])
        return fastavro.schemaless_reader(bytes_io, self.definition)
