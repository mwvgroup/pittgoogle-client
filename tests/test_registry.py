# -*- coding: UTF-8 -*-
"""Unit tests for the registry module."""
import yaml

import pittgoogle

SCHEMA_MANIFEST = yaml.safe_load(
    (pittgoogle.PACKAGE_DIR / "registry_manifests/schemas.yml").read_text()
)


class TestSchemas:
    schemas = pittgoogle.Schemas()

    def test_names(self):
        assert isinstance(self.schemas.names, list)
        truth_names = sorted(schema["name"] for schema in SCHEMA_MANIFEST)
        assert self.schemas.names == truth_names
