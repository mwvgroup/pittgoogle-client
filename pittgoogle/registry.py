# -*- coding: UTF-8 -*-
"""Pitt-Google registries."""
import importlib.resources
import logging
from typing import Final

import yaml
from attrs import define

from . import types_
from .exceptions import SchemaNotFoundError

LOGGER = logging.getLogger(__name__)
PACKAGE_DIR = importlib.resources.files(__package__)
SCHEMA_MANIFEST = yaml.safe_load((PACKAGE_DIR / "registry_manifests/schemas.yml").read_text())


@define(frozen=True)
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


@define(frozen=True)
class Schemas:
    """Registry of schemas used by Pitt-Google.

    Examples:

        .. code-block:: python

            # View list of registered schema names.
            pittgoogle.Schemas.names

            # View more information about the schemas.
            pittgoogle.Schemas.manifest

            # Load a schema (choose a name from above and substitute it below).
            schema = pittgoogle.Schemas.get(schema_name="ztf")

    **For Developers**: :doc:`/for-developers/add-new-schema`

    ----
    """

    @staticmethod
    def get(schema_name: str) -> types_.Schema:
        """Return the schema with name matching `schema_name`.

        Returns:
            Schema:
                Schema from the registry with name matching `schema_name`.

        Raises:
            SchemaNotFoundError:
                If a schema with name matching `schema_name` is not found in the registry.
            SchemaNotFoundError:
                If a schema definition cannot be loaded but one will be required to read the alert bytes.
        """
        # Return the schema with name == schema_name, if one exists.
        for mft_schema in SCHEMA_MANIFEST:
            if mft_schema["name"] == schema_name:
                return types_.Schema._from_yaml(schema_dict=mft_schema)

        # Return the schema with name ~= schema_name, if one exists.
        for mft_schema in SCHEMA_MANIFEST:
            # Case 1: Split by "." and check whether first and last parts match.
            # Catches names like 'lsst.v<MAJOR>_<MINOR>.alert' where users replace '<..>' with custom values.
            split_name, split_mft_name = schema_name.split("."), mft_schema["name"].split(".")
            if all([split_mft_name[i] == split_name[i] for i in [0, -1]]):
                return types_.Schema._from_yaml(schema_dict=mft_schema, name=schema_name)

        # That's all we know how to check so far.
        raise SchemaNotFoundError(
            f"{schema_name} not found. For valid names, see `pittgoogle.Schemas.names`."
        )

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
