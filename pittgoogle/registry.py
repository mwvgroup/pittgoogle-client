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
    """Registry of schemas used by Pitt-Google."""

    @classmethod
    def get(cls, schema_name: str) -> types_.Schema:
        """Return the registered schema called `schema_name`.

        Raises
        ------
        :class:`pittgoogle.exceptions.SchemaNotFoundError`
            if a schema called `schema_name` is not found
        """
        for schema in SCHEMA_MANIFEST:
            if schema["name"] != schema_name:
                continue

            return types_.Schema(
                name=schema["name"],
                description=schema["description"],
                path=PACKAGE_DIR / schema["path"] if schema["path"] is not None else None,
            )

        raise SchemaNotFoundError(
            f"{schema_name} not found. for a list of valid names, use `pittgoogle.Schemas.names()`."
        )

    @classmethod
    def names(cls) -> list[str]:
        """Return the names of all registered schemas."""
        return [schema["name"] for schema in SCHEMA_MANIFEST]
