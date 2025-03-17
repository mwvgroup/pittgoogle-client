# -*- coding: UTF-8 -*-
"""Pitt-Google registries.

.. autosummary::

    ProjectIds
    Schemas

----
"""
import logging
from typing import TYPE_CHECKING, Final, Literal

import attrs
import yaml

from . import __package_path__, exceptions, schema, types_

if TYPE_CHECKING:
    import google.cloud.pubsub_v1

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
        schema_name: Literal[
            "elasticc", "lsst", "lvk", "ztf", "default_schema", None
        ] = "default_schema",
        msg: "google.cloud.pubsub_v1.types.PubsubMessage | types_.PubsubMessageLike | None" = None,
    ) -> schema.Schema:
        """Return the schema with name matching `schema_name`.

        Args:
            schema_name (Literal["elasticc", "lsst", "lvk", "ztf", "default_schema"]):
                Name of the schema to return. Default is ``"default_schema"``.
            msg ("google.cloud.pubsub_v1.types.PubsubMessage | types_.PubsubMessageLike | None"):
                Pub/Sub message to be used to infer the schema version, if provided.

        Returns:
            schema.Schema:
                Schema from the registry with name matching `schema_name`.

        Raises:
            exceptions.SchemaError:
                If a schema named `schema_name` is not found in the registry or cannot be loaded.
        """
        if schema_name is None:
            schema_name = "default"

        try:
            Schema = getattr(schema, schema_name[0].upper() + schema_name[1:] + "Schema")
        except AttributeError:
            raise exceptions.SchemaError(
                f"{schema_name} not found. For valid names, see `pittgoogle.Schemas().names`."
            )

        for manifest in SCHEMA_MANIFEST:
            name = manifest["name"].split(".")[0]  # [FIXME] This is a hack for elasticc.
            if name == schema_name:
                return Schema._from_yaml(yaml_dict=manifest)
                # return Schema._from_yaml(yaml_dict=manifest, msg=msg)

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
