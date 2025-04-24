# -*- coding: UTF-8 -*-
"""Classes to manage alert schemas.

.. autosummary::

    Serializers
    Schema
    DefaultSchema
    ElasticcSchema
    LsstSchema
    LvkSchema
    ZtfSchema

----
"""
import abc
import base64
import io
import json
import logging
import struct
import types
from pathlib import Path
from typing import TYPE_CHECKING, Literal

import attrs
import fastavro
import numpy as np
import yaml

from . import __package_path__, exceptions

if TYPE_CHECKING:
    import google.cloud.pubsub_v1

    from . import Alert, types_

LOGGER = logging.getLogger(__name__)


# --------- Serializers --------- #
@attrs.define
class Serializers:
    @staticmethod
    def serialize_json(alert_dict: dict) -> bytes:
        """Serialize `alert_dict` using the JSON format.

        Args:
            alert_dict (dict):
                The dictionary to be serialized.

        Returns:
            bytes:
                The serialized data in bytes.
        """
        return json.dumps(Serializers._clean_for_json(alert_dict)).encode("utf-8")

    @staticmethod
    def deserialize_json(alert_bytes: bytes) -> dict:
        """Deserialize `alert_bytes` using the JSON format.

        Args:
            alert_bytes (bytes):
                The bytes to be deserialized. This is expected to be serialized as JSON.

        Returns:
            dict:
                The deserialized data in a dictionary.
        """
        return json.loads(alert_bytes)

    @staticmethod
    def serialize_avro(alert_dict: dict, *, schema_definition: dict) -> bytes:
        """Serialize `alert_dict` using the Avro format.

        Args:
            alert_dict (dict):
                The dictionary to be serialized.
        schema_definition (dict):
                The Avro schema definition to use for serialization.

        Returns:
            bytes:
                The serialized data in bytes.
        """
        bytes_io = io.BytesIO()
        fastavro.writer(bytes_io, schema_definition, [alert_dict])
        return bytes_io.getvalue()

    @staticmethod
    def deserialize_avro(alert_bytes: bytes) -> dict:
        """Deserialize `alert_bytes` using the Avro format.

        Args:
            alert_bytes (bytes):
                The bytes to be deserialized. This is expected to be serialized as Avro with the
                schema attached in the header.

        Returns:
            dict:
                The deserialized data in a dictionary.
        """
        with io.BytesIO(alert_bytes) as fin:
            alert_dicts = list(fastavro.reader(fin))  # list with single dict
        if len(alert_dicts) != 1:
            LOGGER.warning(f"Expected 1 Avro record. Found {len(alert_dicts)}.")
        return alert_dicts[0]

    @staticmethod
    def serialize_schemaless_avro(alert_dict: dict, *, schema_definition: dict) -> bytes:
        """Serialize `alert_dict` using the schemaless Avro format.

        Args:
            alert_dict (dict):
                The dictionary to be serialized. The schema is expected to match `schema_definition`.
            schema_definition (dict):
                The Avro schema definition to use for serialization.

        Returns:
            bytes:
                The serialized data in bytes.
        """
        fout = io.BytesIO()
        fastavro.schemaless_writer(fout, schema_definition, alert_dict)
        return fout.getvalue()

    @staticmethod
    def deserialize_schemaless_avro(alert_bytes: bytes, *, schema_definition: dict) -> dict:
        """Deserialize `alert_bytes` using the schemaless Avro format.

        Args:
            alert_bytes (bytes):
                The bytes to be deserialized. This is expected to be serialized as Avro without the
                schema attached in the header. The schema is expected to match `schema_definition`.
            schema_definition (dict):
                The Avro schema definition to use for deserialization.

        Returns:
            dict:
                The deserialized data in a dictionary.
        """
        bytes_io = io.BytesIO(alert_bytes)
        return fastavro.schemaless_reader(bytes_io, schema_definition)

    @staticmethod
    def serialize_confluent_wire_avro(
        alert_dict: dict, *, schema_definition: dict, schema_id: int
    ) -> bytes:
        """Serialize `alert_dict` using the Avro Confluent Wire Format.

        https://docs.confluent.io/platform/current/schema-registry/fundamentals/serdes-develop/index.html#wire-format

        Args:
            alert_dict (dict):
                The dictionary to be serialized. The schema is expected to match `schema_definition`.
            schema_definition (dict):
                The Avro schema definition to use for serialization.
            version_id (int):
                The version ID of the schema. This is a 4-byte integer in big-endian format.
                It will be attached to the header of the serialized data.

        Returns:
            bytes:
                The serialized data in bytes.
        """
        # https://docs.confluent.io/platform/current/schema-registry/fundamentals/serdes-develop/index.html#wire-format
        fout = io.BytesIO()
        fout.write(b"\x00")
        fout.write(struct.pack(">i", schema_id))
        fastavro.schemaless_writer(fout, schema_definition, alert_dict)
        return fout.getvalue()

    @staticmethod
    def deserialize_confluent_wire_avro(alert_bytes: bytes, *, schema_definition: dict) -> dict:
        """Deserialize `alert_bytes` using the Avro Confluent Wire Format.

        https://docs.confluent.io/platform/current/schema-registry/fundamentals/serdes-develop/index.html#wire-format

        Args:
            alert_bytes (bytes):
                The bytes to be deserialized. This is expected to be serialized in Avro Confluent
                Wire Format. The schema is expected to match `schema_definition`.
            schema_definition (dict):
                The Avro schema definition to use for deserialization.

        Returns:
            dict:
                The deserialized data in a dictionary.
        """
        # https://docs.confluent.io/platform/current/schema-registry/fundamentals/serdes-develop/index.html#wire-format
        bytes_io = io.BytesIO(alert_bytes[5:])
        return fastavro.schemaless_reader(bytes_io, schema_definition)

    @staticmethod
    def _clean_for_json(
        value: str | int | float | bytes | list | dict | None,
    ) -> str | int | float | list | dict | None:
        """Coerce `value` to a format suitable for json serialization.

        Args:
            value (str, int, float, bytes, list, dict, or None):
                The value to be cleaned. str, int, float (except NaN), and None types are
                returned unchanged. `None` is returned if `value` is consistent with NaN.
                bytes types are returned as base64-encoded strings. If list or dict, this
                method will be called recursively on each element/item.

        Returns:
            str, int, float, list, dict, or None:
                `value` with NaN replaced by None. Replacement is recursive if `value` is a list or dict.

        Raises:
            TypeError:
                If `value` is not a str, int, float, bytes, list, or dict.
        """
        # Return value suitable for json serialization.
        if isinstance(value, (str, int, types.NoneType)):
            return value
        if isinstance(value, float):
            return value if not np.isnan(value) else None
        if isinstance(value, bytes):
            return base64.b64encode(value).decode("utf-8")

        # Recurse.
        if isinstance(value, list):
            return [Serializers._clean_for_json(v) for v in value]
        if isinstance(value, dict):
            return {k: Serializers._clean_for_json(v) for k, v in value.items()}

        # That's all we know how to deal with right now.
        raise TypeError(f"Unrecognized type '{type(value)}' ({value})")


# --------- Default Schema Definitions --------- #
@attrs.define(kw_only=True)
class Schema(abc.ABC):
    """Class for an individual schema.

    Do not call this class's constructor directly. Instead, load a schema using the registry
    :class:`pittgoogle.registry.Schemas`.

    ----
    """

    # String _under_ field definition will cause field to appear as a property in rendered docs.
    name: str = attrs.field()
    """Name of the schema. This is typically the name of the survey as well."""
    description: str = attrs.field()
    """A description of the schema."""
    origin: str = attrs.field()
    """Pointer to the schema's origin. Typically this is a URL to a repo maintained by the survey."""
    serializer: Literal["json", "avro"] = attrs.field()
    """Whether to serialize the dict to JSON or Avro when, e.g., publishing a Pub/Sub message."""
    deserializer: Literal["json", "avro"] = attrs.field()
    """Whether to use a JSON or Avro to deserialize when decoding alert_bytes -> alert_dict."""
    version: str | None = attrs.field(default=None)
    """Version of the schema, or None."""
    version_id: str | None = attrs.field(default=None)
    """Version ID of the schema, or None. Currently only used for class:`_ConfluentWireAvroSchema`."""
    definition: dict | None = attrs.field(default=None)
    """The schema definition used to serialize and deserialize the alert bytes, if one is required."""
    path: Path | None = attrs.field(default=None)
    """Path to a file containing the schema definition."""
    filter_map: dict = attrs.field(factory=dict)
    """Mapping of the filter name as stored in the alert (often an int) to the common name (often a string)."""
    # The rest don't need string descriptions because we will define them as explicit properties.
    _map: dict | None = attrs.field(default=None, init=False)

    @classmethod
    @abc.abstractmethod
    def _from_yaml(cls, yaml_dict: dict, *, alert_bytes: bytes | None = None):
        """Create a :class:`Schema` object. This class method must be implemented by subclasses.

        Args:
            yaml_dict (dict):
                A dictionary containing the schema information. This should be one entry from the
                registry's 'schemas.yml' file.
            alert_bytes (bytes or None, optional):
                Message data, if available. Some schemas will use this to infer the schema version.

        Returns:
            Schema
        """

    @abc.abstractmethod
    def serialize(
        self, alert_dict: dict, *, serializer: Literal["json", "avro", None] = None
    ) -> bytes:
        """Serialize `alert_dict`. This method must be implemented by subclasses.

        Args:
            alert_dict (dict):
                The dictionary to be serialized.
            serializer (str or None, optional):
                Whether to serialize the dict using Avro or JSON. If not None, this will override
                the `serializer` property and is subject to the same conditions.

        Returns:
            bytes:
                The serialized data in bytes.
        """

    @abc.abstractmethod
    def deserialize(self, alert_bytes: bytes) -> dict:
        """Deserialize `alert_bytes`. This method must be implemented by subclasses.

        Args:
            alert_bytes (bytes):
                The bytes to be deserialized.

        Returns:
            dict:
                A dictionary representing the deserialized `alert_bytes`.
        """

    @abc.abstractmethod
    def _name_in_bucket(_alert: "Alert") -> None:
        """Construct the name of the Google Cloud Storage object."""

    @property
    def survey(self) -> str:
        return self.name

    @property
    def map(self) -> dict:
        """Mapping of Pitt-Google's generic field names to survey-specific field names."""
        if self._map is None:
            yml = __package_path__ / "schemas" / "maps" / f"{self.survey}.yml"
            try:
                self._map = yaml.safe_load(yml.read_text())
            except FileNotFoundError:
                raise ValueError(f"no schema map found for schema name '{self.name}'")
        return self._map


@attrs.define(kw_only=True)
class DefaultSchema(Schema):
    """Default schema to serialize and deserialize alert bytes."""

    serializer: Literal["json", "avro"] = attrs.field(default="json")
    """Whether to serialize the alert_dict to JSON (default) or Avro when, e.g., publishing a Pub/Sub message.
    If "avro", the user must supply the schema definition by setting :meth:`Schema.definition`."""
    deserializer: Literal["json", "avro"] = attrs.field(default="json")
    """Whether to use a JSON (default) or Avro to deserialize when decoding `alert_bytes` -> `alert_dict`.
    If "avro", this `pittgoogle.Schema` will expect the Avro schema to be attached to `alert_bytes` in the header."""

    @classmethod
    def _from_yaml(cls, yaml_dict: dict, *, alert_bytes: bytes | None = None):
        """Create a schema object from `yaml_dict`.

        Args:
            yaml_dict (dict):
                A dictionary containing the schema information. This should be one entry from the
                registry's 'schemas.yml' file.
            alert_bytes (bytes or None, optional):
                Message data, if available. This is unused and not necessary for this schema.

        Returns:
            Schema
        """
        schema = cls(**yaml_dict)

        # Resolve the path. If it is not None, it is expected to be the path to
        # a ".avsc" file relative to the pittgoogle package directory.
        schema.path = __package_path__ / schema.path if schema.path is not None else None

        # Load the avro schema definition, if the file exists. Fallback to None.
        invalid_path = (
            (schema.path is None) or (schema.path.suffix != ".avsc") or (not schema.path.is_file())
        )
        schema.definition = None if invalid_path else fastavro.schema.load_schema(schema.path)

        return schema

    def serialize(
        self, alert_dict: dict, *, serializer: Literal["json", "avro", None] = None
    ) -> bytes:
        """Serialize the `alert_dict`.

        Args:
            alert_dict (dict):
                The dictionary to be serialized.
            serializer (str or None, optional):
                Whether to serialize the dict using Avro or JSON. If not None, this will override
                the `serializer` property and is subject to the same conditions.

        Returns:
            bytes:
                The serialized data in bytes.
        """
        _serializer = serializer or self.serializer
        if _serializer == "json":
            return Serializers.serialize_json(alert_dict)
        return Serializers.serialize_avro(alert_dict, schema_definition=self.definition)

    def deserialize(self, alert_bytes: bytes) -> dict:
        """Deserialize `alert_bytes` using JSON or Avro format as defined by the `deserializer` property.

        Args:
            alert_bytes (bytes):
                The bytes to be deserialized.

        Returns:
            A dictionary representing the deserialized `alert_bytes`.
        """
        if self.deserializer == "json":
            return Serializers.deserialize_json(alert_bytes)
        return Serializers.deserialize_avro(alert_bytes)

    def _name_in_bucket(_alert: "Alert") -> None:
        """Construct the name of the Google Cloud Storage object."""
        raise NotImplementedError("Name syntax is unknown.")


# --------- Survey Schema Definitions --------- #
@attrs.define(kw_only=True)
class ElasticcSchema(Schema):
    """Schema for ELAsTiCC alerts."""

    serializer: Literal["json", "avro"] = attrs.field(default="avro")
    """Whether to serialize the dict to Avro (default) or JSON when, e.g., publishing a Pub/Sub message.
    If "avro", this schema will use the schemaless Avro format."""
    deserializer: Literal["json", "avro"] = attrs.field(default="avro")
    """Whether to use a Avro (default) or JSON to deserialize when decoding alert_bytes -> alert_dict.
    If "avro", this schema will use the schemaless Avro format."""

    @classmethod
    def _from_yaml(cls, yaml_dict: dict, *, alert_bytes: bytes | None = None):
        """Create a schema object from `yaml_dict`.

        Args:
            yaml_dict (dict):
                A dictionary containing the schema information, loaded from the registry's 'schemas.yml' file.
        alert_bytes (bytes or None, optional):
            Message data, if available. This is unused and not necessary for this schema.

        Returns:
            Schema
        """
        schema = cls(**yaml_dict)
        schema.path = __package_path__ / schema.path
        schema.definition = fastavro.schema.load_schema(schema.path)
        return schema

    def serialize(
        self, alert_dict: dict, *, serializer: Literal["json", "avro", None] = None
    ) -> bytes:
        """Serialize the `alert_dict`.

        Args:
            alert_dict (dict):
                The dictionary to be serialized.
            serializer (str or None, optional):
                Whether to serialize the dict using Avro or JSON. If not None, this will override
                :meth:`ElasticcSchema.serializer` and is subject to the same conditions.

        Returns:
            bytes:
                The serialized data in bytes.
        """
        _serializer = serializer or self.serializer
        if _serializer == "json":
            return Serializers.serialize_json(alert_dict)
        return Serializers.serialize_schemaless_avro(alert_dict, schema_definition=self.definition)

    def deserialize(self, alert_bytes: bytes) -> dict:
        """Deserialize `alert_bytes` using JSON or Avro format as defined by :meth:`ElasticcSchema.deserializer`.

        Args:
            alert_bytes (bytes):
                The bytes to be deserialized.

        Returns:
            A dictionary representing the deserialized `alert_bytes`.
        """
        if self.deserializer == "json":
            return Serializers.deserialize_json(alert_bytes)
        return Serializers.deserialize_schemaless_avro(
            alert_bytes, schema_definition=self.definition
        )

    def _name_in_bucket(_alert: "Alert") -> None:
        """Construct the name of the Google Cloud Storage object."""
        raise NotImplementedError("Name syntax is unknown.")


@attrs.define(kw_only=True)
class LsstSchema(Schema):
    """Schema for LSST alerts."""

    serializer: Literal["json", "avro"] = attrs.field(default="avro")
    """Whether to serialize the dict to Avro (default) or JSON when, e.g., publishing a Pub/Sub message.
    If "avro", this schema will use the Avro Confluent Wire Format
    (https://docs.confluent.io/platform/current/schema-registry/fundamentals/serdes-develop/index.html#wire-format)."""
    deserializer: Literal["json", "avro"] = attrs.field(default="avro")
    """Whether to use Avro (default) or JSON to deserialize when decoding alert_bytes -> alert_dict.
    If "avro", this schema will use the Avro Confluent Wire Format
    (https://docs.confluent.io/platform/current/schema-registry/fundamentals/serdes-develop/index.html#wire-format)."""

    @classmethod
    def _from_yaml(cls, yaml_dict: dict, *, alert_bytes: bytes | None = None):
        """Create a schema object from `yaml_dict`.

        Args:
            yaml_dict (dict):
                A dictionary containing the schema information, loaded from the registry's 'schemas.yml' file.
            alert_bytes (bytes or None, optional):
                Message data. This is needed in order to infer the schema version. If not provided,
                methods such as :meth:`LsstSchema.serialize` (if avro), :meth:`LsstSchema.deserialize` (if avro),
                and :meth:`LsstSchema._name_in_bucket` will raise a :class:`pittgoogle.exceptions.SchemaError`.

        Returns:
            Schema
        """
        schema = cls(**yaml_dict)

        if alert_bytes is None:
            LOGGER.warning(
                "No alert_bytes provided. Cannot infer schema version. "
                "Methods that rely on it will be unavailable."
            )
            return schema

        # Get the schema ID out of the avro header and use it to construct the schema version.
        # LSST's syntax is: schema-id = 703 (int) --> schema-version = 'v7_3'
        _, version_id = struct.Struct(">bi").unpack(alert_bytes[:5])
        schema.version_id = version_id
        major, minor = str(version_id).split("0", maxsplit=1)  # Convert, eg, 703 -> 'v7_3'
        schema.version = f"v{major}_{minor}"

        if schema.version not in ["v7_0", "v7_1", "v7_2", "v7_3", "v7_4"]:
            raise exceptions.SchemaError(f"Schema definition not found for {schema.version}.")

        # Resolve the path and load the schema definition.
        schema_path = schema.path.replace("MAJOR", major).replace("MINOR", minor)
        schema.path = __package_path__ / schema_path
        schema.definition = fastavro.schema.load_schema(schema.path)

        return schema

    def serialize(
        self, alert_dict: dict, *, serializer: Literal["json", "avro", None] = None
    ) -> bytes:
        """Serialize the `alert_dict`.

        Args:
            alert_dict (dict):
                The dictionary to be serialized.
            serializer (str or None, optional):
                Whether to serialize the dict using Avro or JSON. If not None, this will override
                :meth:`LsstSchema.serializer` and is subject to the same conditions.

        Returns:
            bytes:
                The serialized data in bytes.

        Raises:
            exceptions.SchemaError:
                If the schema version or definition are unavailable and Avro serialization is requested.
        """
        _serializer = serializer or self.serializer
        if _serializer == "json":
            return Serializers.serialize_json(alert_dict)

        if self.version is None or self.definition is None:
            raise exceptions.SchemaError(
                "No Avro schema information is available. Cannot serialize to Avro."
            )

        # Reconstruct LSST's schema ID from the version string. Convert, eg, 'v7_3' -> 703.
        schema_id = int("0".join(self.version.strip("v").split("_")))
        return Serializers.serialize_confluent_wire_avro(
            alert_dict, schema_definition=self.definition, schema_id=schema_id
        )

    def deserialize(self, alert_bytes: bytes) -> dict:
        """Deserialize `alert_bytes` using JSON or Avro format as defined by :meth:`LsstSchema.deserializer`.

        Args:
            alert_bytes (bytes):
                The bytes to be deserialized.

        Returns:
            A dictionary representing the deserialized `alert_bytes`.
        """
        if self.deserializer == "json":
            return Serializers.deserialize_json(alert_bytes)

        if self.definition is None:
            raise exceptions.SchemaError(
                "No schema definition available. Cannot deserialize Avro."
            )

        return Serializers.deserialize_confluent_wire_avro(
            alert_bytes, schema_definition=self.definition
        )

    @staticmethod
    def _name_in_bucket(alert: "Alert"):
        if alert.schema.version is None:
            raise exceptions.SchemaError(
                "No version information available. Cannot construct object name."
            )

        import astropy.time  # always lazy-load astropy

        _date = astropy.time.Time(alert.get("mjd"), format="mjd").datetime.strftime("%Y-%m-%d")
        return f"{alert.schema.version}/{_date}/{alert.objectid}/{alert.sourceid}.avro"


@attrs.define(kw_only=True)
class LvkSchema(DefaultSchema):
    """Schema for LVK alerts."""


@attrs.define(kw_only=True)
class ZtfSchema(DefaultSchema):
    """Schema for ZTF alerts."""

    deserializer: Literal["json", "avro"] = attrs.field(default="avro")
    """Whether to use a Avro (default) or JSON to deserialize when decoding `alert_bytes` -> `alert_dict`.
    If "avro", this `pittgoogle.Schema` will expect the Avro schema to be attached to `alert_bytes` in the header."""
