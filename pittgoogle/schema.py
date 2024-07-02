# -*- coding: UTF-8 -*-
"""Classes to manage alert schemas."""
import importlib.resources
import logging
import re
from pathlib import Path

import fastavro
import yaml
from attrs import converters, define, field, evolve

from . import exceptions

LOGGER = logging.getLogger(__name__)
PACKAGE_DIR = importlib.resources.files(__package__)


@define(kw_only=True)
class SchemaHelpers:
    """Class to organize helper functions.

    This class is not intended to be used directly, except by developers adding support for a new schema.

    For Developers:

        When a user requests a schema from the registry, the class method :meth:`Schema._from_yaml` is called.
        The method will partially initialize the :class:`Schema` using the registry's `schemas.yml` file,
        and then pass it to one of the :class:`SchemaHelpers` methods to finish the initialization.

        If you are adding support for a new schema, the value you enter for the ``helper`` field in the
        `schemas.yml` file should be the name of the :class:`SchemaHelpers` method to be used to finish
        initializing the new :class:`Schema`.

        Methods in this class are expected to accept a partially initialized :class:`Schema`,
        finish initializing it by (e.g.,) loading the schema definition into :attr:`Schema.definition`,
        and then return the fully-initialized :class:`Schema`.

    ----
    """

    @staticmethod
    def default_schema_helper(schema: "Schema") -> "Schema":
        """Resolve `schema.path`. If it points to a valid ".avsc" file, load it into `schema.avsc`."""
        # Resolve the path. If it is not None, this helper expects it to be the path to
        # a ".avsc" file relative to the pittgoogle package directory.
        schema.path = PACKAGE_DIR / schema.path if schema.path is not None else None

        # Load the avro schema, if the file exists.
        invalid_path = (
            (schema.path is None) or (schema.path.suffix != ".avsc") or (not schema.path.is_file())
        )
        if invalid_path:
            schema.definition = None
        else:
            schema.definition = fastavro.schema.load_schema(schema.path)

        return schema

    @staticmethod
    def lsst_schema_helper(schema: "Schema") -> "Schema":
        """Load the Avro schema definition using the ``lsst.alert.packet`` package.

        Raises:
            SchemaNotFoundError:
                If an LSST schema called ``schema.name`` cannot be loaded. An error is raised
                because the LSST alert bytes are schemaless, so ``schema.definition`` will be
                required in order to deserialize the alert.
        """
        import lsst.alert.packet.schema

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
            raise exceptions.SchemaNotFoundError(msg)

        schema_dir = Path(lsst.alert.packet.schema.get_schema_path(major, minor))
        schema.path = schema_dir / f"{schema.name}.avsc"

        try:
            schema.definition = lsst.alert.packet.schema.Schema.from_file(schema.path).definition
        except fastavro.repository.SchemaRepositoryError:
            msg = f"Unable to load the schema. {version_msg}"
            raise exceptions.SchemaNotFoundError(msg)

        return schema


@define(kw_only=True)
class Schema:
    """Class for an individual schema.

    Do not call this class's constructor directly. Instead, load a schema using the registry
    :class:`pittgoogle.registry.Schemas`.

    ----
    """

    # String _under_ field definition will cause field to appear as a property in rendered docs.
    name: str = field()
    """Name of the schema."""
    origin: str = field()
    """Pointer to the schema's origin. Typically this is a URL to a repo maintained by the survey."""
    description: str = field()
    """A description of the schema."""
    definition: dict | None = field(default=None)
    """The schema definition used to serialize and deserialize the alert bytes, if one is required."""
    schemaless_alert_bytes: bool = field(default=False, converter=converters.to_bool)
    """Whether the alert bytes are schemaless. If True, a valid `definition` is required to
    serialize or deserialize the alert packet bytes."""
    _helper: str = field(default="default_schema_helper")
    """Name of the method in :class:`SchemaHelpers` used to load this schema."""
    path: Path | None = field(default=None)
    """Path where the helper can find the schema, if needed."""
    filter_map: dict = field(factory=dict)
    """Mapping of the filter name as stored in the alert (often an int) to the common name (often a string)."""
    # The rest don't need string descriptions because we will define them as explicit properties.
    _survey: str | None = field(default=None)
    # _map is important, but don't accept it as an init arg. We'll load it from a yaml file later.
    _map: dict | None = field(default=None, init=False)

    @classmethod
    def _from_yaml(cls, schema_dict: dict, **evolve_schema_dict) -> "Schema":
        """Create a :class:`Schema` object from an entry in the registry's `schemas.yml` file.

        Args:
            schema_dict (dict):
                A dictionary containing the schema information.
            **evolve_schema_dict:
                Additional keyword arguments that will override entries in ``schema_dict``.

        Returns:
            Schema:
                The created `Schema` object.
        """
        # initialize the class, then let the helper finish up
        schema = evolve(cls(**schema_dict), **evolve_schema_dict)
        helper = getattr(SchemaHelpers, schema._helper)
        return helper(schema)

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
