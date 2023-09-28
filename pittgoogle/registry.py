# -*- coding: UTF-8 -*-
"""Pitt-Google registries."""
import importlib.resources
import logging
from typing import ClassVar

from attrs import define

from . import types_
from .exceptions import SchemaNotFoundError


LOGGER = logging.getLogger(__name__)
PACKAGE_DIR = importlib.resources.files(__package__)


@define(frozen=True)
class ProjectIds:
    """Registry of Google Cloud Project IDs."""

    pittgoogle: ClassVar[str] = "ardent-cycling-243415"
    """Pitt-Google's production project."""

    pittgoogle_dev: ClassVar[str] = "avid-heading-329016"
    """Pitt-Google's development project."""

    # pittgoogle_billing: ClassVar[str] = "light-cycle-328823"
    # """Pitt-Google's billing project."""

    elasticc: ClassVar[str] = "elasticc-challenge"
    """Project running a classifier for ELAsTiCC alerts and reporting to DESC."""


@define(frozen=True)
class Schemas:
    """Registry of schemas used by Pitt-Google."""

    # dict defining the schemas in the registry
    # naming conventions:
    # - schema names are expected to start with the name of the survey
    # - if the survey has more than one schema, the survey name should be followed by a ".",
    #   followed by schema-specific specifier(s)
    # - if an avro schema file is being registered with the schema (using the `path` arg), it is
    #   recommended that the file have the same name (path stem) as the schema. the file name
    #   must end with ".avsc".
    dict: ClassVar[dict] = {
        "elasticc.v0_9_1.alert": types_.Schema(
            name="elasticc.v0_9_1.alert",
            description="Avro schema of alerts published by ELAsTiCC.",
            path=PACKAGE_DIR / f"schemas/elasticc/elasticc.v0_9_1.alert.avsc",
        ),
        "elasticc.v0_9_1.brokerClassification": types_.Schema(
            name="elasticc.v0_9_1.brokerClassification",
            description="Avro schema of alerts to be sent to DESC containing classifications of ELAsTiCC alerts.",
            path=PACKAGE_DIR / f"schemas/elasticc/elasticc.v0_9_1.brokerClassification.avsc",
        ),
        "ztf": types_.Schema(
            name="ztf",
            description=(
                "ZTF schema. The ZTF survey publishes alerts in Avro format with the schema attached "
                "in the header. Pitt-Google publishes ZTF alerts in json format. This schema covers "
                "both cases."  # [TODO]
            ),
            path=None,
        ),
    }
    """Dict defining the schemas in the registry."""

    @classmethod
    def names(cls) -> list[str]:
        """Return the names of all registered schemas."""
        return list(cls.dict.keys())

    @classmethod
    def get(cls, schema_name: str) -> types_.Schema:
        """Return the registered schema called `schema_name`.

        Raises
        ------
        :class:`pittgoogle.exceptions.SchemaNotFoundError`
            if a schema called `schema_name` is not found
        """
        # if there is no registered schema with this name, raise an error
        schema = cls.dict.get(schema_name)
        if schema is None:
            raise SchemaNotFoundError(
                f"{schema_name} not found. for a list of valid names, use `pittgoogle.Schemas.names()`."
            )
        return schema
