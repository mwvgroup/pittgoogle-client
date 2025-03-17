# -*- coding: UTF-8 -*-
"""Pitt-Google registries.

.. autosummary::

    ProjectIds
    Schemas

----
"""
import logging
from typing import Final, Literal, Type

import attrs
import yaml

from . import __package_path__, exceptions, schema


LOGGER = logging.getLogger(__name__)

# Load the schema manifest as a list of dicts sorted by key.
manifest_yaml = (__package_path__ / "registry_manifests" / "schemas.yml").read_text()
SCHEMA_MANIFEST = sorted(yaml.safe_load(manifest_yaml), key=lambda schema: schema["name"])


@attrs.define(frozen=True)
class ProjectIds:
    """Registry of Google Cloud Project IDs."""

    pittgoogle: Final[str] = "ardent-cycling-243415"
    """Pitt-Google's production project."""

    pittgoogle_dev: Final[str] = "avid-heading-329016"
    """Pitt-Google's testing and development project."""

    # pittgoogle_billing: Final[str] = "light-cycle-328823"
    # """Pitt-Google's billing project."""

    elasticc: Final[str] = "elasticc-challenge"
    """Project running classifiers for ELAsTiCC alerts and reporting to DESC."""


@attrs.define(frozen=True)
class Schemas:
    """Registry of schemas used by Pitt-Google.

    Examples:

        .. code-block:: python

            # View list of registered schema names.
            pittgoogle.Schemas().names

            # Load a schema (choose a name from above and substitute it below).
            schema = pittgoogle.Schemas().get(schema_name="ztf")

            # View more information about all the schemas.
            pittgoogle.Schemas().manifest

    **For Developers**: :doc:`/for-developers/add-new-schema`

    ----
    """

    @staticmethod
    def get(
        schema_name: Literal["elasticc", "lsst", "lvk", "ztf", "default", None] = "default",
        alert_bytes: bytes | None = None,
    ) -> schema.Schema:
        """Return the schema with name matching `schema_name`.

        Args:
            schema_name (str or None, optional):
                Name of the schema to return. If None, the default schema is returned.
            alert_bytes (bytes or None, optional):
                Message data, if available. Some schemas will use this to infer the schema version.

        Returns:
            schema.Schema:
                Schema from the registry with name matching `schema_name`.

        Raises:
            exceptions.SchemaError:
                If a schema named `schema_name` is not found in the registry or cannot be loaded.
        """
        if schema_name is None:
            schema_name = "default"

        for yaml_dict in SCHEMA_MANIFEST:
            name = yaml_dict["name"].split(".")[0]  # [FIXME] This is a hack for elasticc.
            if name == schema_name:
                _Schema = Schemas._get_class(schema_name)
                return _Schema._from_yaml(yaml_dict=yaml_dict, alert_bytes=alert_bytes)

        raise exceptions.SchemaError(
            f"'{schema_name}' not found. For valid names, see `pittgoogle.Schemas().names`."
        )

    @staticmethod
    def _get_class(schema_name: str) -> Type[schema.Schema]:
        """Return the schema class with name matching `schema_name`.

        Args:
            schema_name (str):
                Name of the schema to return.

        Returns:
            schema.Schema:
                Schema from the registry with name matching `schema_name`.

        Raises:
            exceptions.SchemaError:
                If a schema named `schema_name` is not found in the registry or cannot be loaded.
        """
        class_name = schema_name[0].upper() + schema_name[1:] + "Schema"
        err_msg = (
            f"{class_name} not found for schema_name='{schema_name}'. ",
            "For valid names, see `pittgoogle.Schemas().names`.",
        )
        try:
            return getattr(schema, class_name)
        except AttributeError as exc:
            raise exceptions.SchemaError(err_msg) from exc

    @property
    def names(self) -> list[str]:
        """Names of all registered schemas.

        A name from this list can be used with the :meth:`Schemas.get` method to load a schema.
        Capital letters between angle brackets indicate that you should substitute your own
        values. For example, to use the LSST schema listed here as ``"lsst.v<MAJOR>_<MINOR>.alert"``,
        choose your own major and minor versions and use like ``pittgoogle.Schemas.get("lsst.v7_1.alert")``.
        View available schema versions by following the `origin` link in :attr:`Schemas.manifest`.
        """
        return [schema["name"] for schema in SCHEMA_MANIFEST]

    @property
    def manifest(self) -> list[dict]:
        """List of dicts containing the registration information of all known schemas."""
        return SCHEMA_MANIFEST
