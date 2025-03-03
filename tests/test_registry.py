# -*- coding: UTF-8 -*-
"""Unit tests for the registry module."""
import yaml

import pittgoogle

# Load the schema manifest as a list of dicts sorted by key.
manifest_yaml = pittgoogle.__package_path__ / "registry_manifests/schemas.yml"
SCHEMA_MANIFEST = yaml.safe_load(manifest_yaml.read_text())


class TestSchemas:
    schemas = pittgoogle.Schemas()

    def test_names(self):
        assert isinstance(self.schemas.names, list)
        truth_names = sorted(schema["name"] for schema in SCHEMA_MANIFEST)
        assert self.schemas.names == truth_names
