# -*- coding: UTF-8 -*-
"""Unit tests for the registry module."""
import io
import struct

import pytest
import yaml

import pittgoogle

# Load the schema manifest as a list of dicts sorted by key.
manifest_yaml = pittgoogle.__package_path__ / "registry_manifests/schemas.yml"
SCHEMA_MANIFEST = yaml.safe_load(manifest_yaml.read_text())


class TestRegistrySchemas:
    schemas = pittgoogle.Schemas()

    def test_names(self):
        assert isinstance(self.schemas.names, list)
        truth_names = sorted(schema["name"] for schema in SCHEMA_MANIFEST)
        assert self.schemas.names == truth_names

    def test_manifest(self):
        assert isinstance(self.schemas.manifest, list)
        truth_manifest = sorted(SCHEMA_MANIFEST, key=lambda schema: schema["name"])
        assert self.schemas.manifest == truth_manifest
        required_properties = ["name", "description", "origin"]
        for schema in self.schemas.manifest:
            assert isinstance(schema, dict)
            assert all(key in schema for key in required_properties)

    def test_get_default_schema(self):
        schema = self.schemas.get(schema_name=None)
        assert isinstance(schema, pittgoogle.schema.Schema)

    @pytest.mark.parametrize("schema_name", [schema["name"] for schema in SCHEMA_MANIFEST])
    def test_get_schema_by_name(self, schema_name):
        schema = self.schemas.get(schema_name=schema_name)
        assert isinstance(schema, pittgoogle.schema.Schema)

    def test_get_schema_with_bad_name(self, survey_names):
        with pytest.raises(pittgoogle.exceptions.SchemaError):
            self.schemas.get(schema_name="nonexistent_schema")
        for survey in survey_names:
            with pytest.raises(pittgoogle.exceptions.SchemaError):
                self.schemas.get(schema_name=f"{survey}.vNONE.alert")

    def test_serialize_without_definition(self):
        schema = self.schemas.get(schema_name="lsst")
        with pytest.raises(pittgoogle.exceptions.SchemaError, match="Schema definition unknown."):
            schema.serialize({})

    def test_unsupported_version_lsst(self):
        unsuported_version_id = 601
        # LSST schemas get the version from the alert bytes.
        # Write an avro header with the unsupported version_id.
        fout = io.BytesIO()
        fout.write(b"\x00")
        fout.write(struct.pack(">i", unsuported_version_id))
        # Try to load the schema definition and show that it raises an error.
        schema = pittgoogle.Alert.from_dict({"key": "value"}, schema_name="lsst").schema
        with pytest.raises(pittgoogle.exceptions.SchemaError, match="Schema definition not found"):
            schema._init_from_bytes(schema=schema, alert_bytes=fout.getvalue())
