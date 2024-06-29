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

    Example:

    .. code-block:: python

        # View list of registered schema names.
        pittgoogle.Schemas.names

        # Load a schema (choose a name from above and substitute it below).
        schema = pittgoogle.Schemas.get(schema_name="ztf")


    For Developers:

    Register a New Schema

    Schemas are defined in the yaml file [registry_manifests/schemas.yml](registry_manifests/schemas.yml).
    To register a new schema, add a section to that file.
    The fields are the same as those of a :class:`pittgoogle.types_.Schema`.
    The `helper` field value must be the name of a valid `*_helper` method in :class:`pittgoogle.types_.Schema`.
    If a suitable method does not already exist for your schema, add one by following the default as an example.
    If your new helper method requires a new dependency, be sure to add it following
    :doc:`/main/for-developers/manage-dependencies-poetry`
    If you want to include your schema's ".avsc" file with the pittgoogle package, be sure to
    commit the file(s) to the repo under the "schemas" directory.
    """

    @classmethod
    def get(cls, schema_name: str) -> types_.Schema:
        """Return the schema registered with name `schema_name`.

        Raises
        ------
        :class:`pittgoogle.exceptions.SchemaNotFoundError`
            if a schema called `schema_name` is not found
        """
        for schema in SCHEMA_MANIFEST:
            if schema["name"] != schema_name:
                continue
            return types_.Schema.from_yaml(schema_dict=schema)

        raise SchemaNotFoundError(
            f"{schema_name} not found. for a list of valid names, use `pittgoogle.Schemas.names()`."
        )

    @staticmethod
    def names() -> list[str]:
        """Return the names of all registered schemas."""
        return [schema["name"] for schema in SCHEMA_MANIFEST]
