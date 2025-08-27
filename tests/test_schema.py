# -*- coding: UTF-8 -*-
"""Unit tests for the registry module."""
import json

import numpy as np
import pytest

import pittgoogle


class TestSerialize:
    def test_sample_alerts(self, sample_alerts):
        for sample_alert in sample_alerts:
            schema = pittgoogle.Schemas.get(
                sample_alert.schema_name, alert_bytes=sample_alert.bytes_
            )
            assert isinstance(schema, pittgoogle.schema.Schema)

            # Skipping json default serializer for now.
            if schema.serializer == "json":
                continue

            # Test the default serializer.
            serialized_dict = schema.serialize(sample_alert.dict_)
            serialized_dict = serialized_dict.replace(b"\n", b"").replace(b" ", b"")
            sample_alert_bytes = sample_alert.bytes_.replace(b"\n", b"").replace(b" ", b"")
            assert serialized_dict == sample_alert_bytes

            # Now switch to the non-default serializer. Need to drop cutouts.
            cutout_keys = (
                sample_alert.pgalert.get_key(key)
                for key in ["cutout_difference", "cutout_science", "cutout_template"]
            )
            sample_alert_dict = {
                k: v for k, v in sample_alert.dict_.items() if k not in cutout_keys
            }
            # Values containing invalid JSON types in sample_alert_dict are converted to valid JSON when serialized.
            # Convert sample_alert_dict to a JSON-compatible form so we can test that serialization produces the
            # correct JSON output. Otherwise, the assertion would fail due to type mismatches.
            expected_json_dict = pittgoogle.schema.Serializers._clean_for_json(sample_alert_dict)
            serialized_dict = schema.serialize(sample_alert_dict, serializer="json")
            assert json.loads(serialized_dict) == expected_json_dict


class TestDeserialize:
    def test_sample_paths(self, sample_alerts):
        for sample_alert in sample_alerts:
            schema = pittgoogle.Schemas.get(
                sample_alert.schema_name, alert_bytes=sample_alert.bytes_
            )
            assert isinstance(schema, pittgoogle.schema.Schema)

            # Test the default deserializer.
            deserialized_bytes = schema.deserialize(sample_alert.bytes_)
            assert deserialized_bytes == sample_alert.dict_

            # Now switch to the non-default deserializer.
            alert_dict = {"objectid": 67890, "sourceid": 1234567890}
            if schema.deserializer == "avro":
                alert_bytes = json.dumps(alert_dict).encode("utf-8")
                schema.deserializer = "json"
                deserialized_bytes = schema.deserialize(alert_bytes)
                assert deserialized_bytes == alert_dict
            # Skipping json -> avro for now.


class TestCleanForJson:
    def test_clean_for_json_str(self):
        assert pittgoogle.schema.Serializers._clean_for_json("test") == "test"

    def test_clean_for_json_int(self):
        assert pittgoogle.schema.Serializers._clean_for_json(123) == 123

    def test_clean_for_json_float(self):
        assert pittgoogle.schema.Serializers._clean_for_json(1.23) == 1.23

    def test_clean_for_json_nan(self):
        assert pittgoogle.schema.Serializers._clean_for_json(np.nan) is None

    def test_clean_for_json_bytes(self):
        assert pittgoogle.schema.Serializers._clean_for_json(b"test") == "dGVzdA=="

    def test_clean_for_json_list(self):
        input_, expected_output = [1, 2.3, "test", np.nan], [1, 2.3, "test", None]
        assert pittgoogle.schema.Serializers._clean_for_json(input_) == expected_output

    def test_clean_for_json_dict(self):
        input_ = {"a": 1, "b": 2.3, "c": "test", "d": np.nan}
        expected_output = {"a": 1, "b": 2.3, "c": "test", "d": None}
        assert pittgoogle.schema.Serializers._clean_for_json(input_) == expected_output

    def test_clean_for_json_none(self):
        assert pittgoogle.schema.Serializers._clean_for_json(None) is None

    def test_clean_for_json_nested(self):
        input_ = {"a": [1, np.nan, {"b": b"test"}]}
        expected = {"a": [1, None, {"b": "dGVzdA=="}]}
        assert pittgoogle.schema.Serializers._clean_for_json(input_) == expected

    def test_clean_for_json_unrecognized_type(self):
        class UnrecognizedType:
            pass

        with pytest.raises(TypeError):
            pittgoogle.schema.Serializers._clean_for_json(UnrecognizedType())


class TestLvkSchema:
    def test_name_in_bucket(self, sample_alerts_lvk):
        for sample_alert in sample_alerts_lvk:
            alert = sample_alert.pgalert
            filename = alert.schema._name_in_bucket(alert=alert)
            assert isinstance(filename, str)
            assert filename.startswith("v")
            assert len(filename.split("/")) == 3
            assert filename.endswith(".json")

        alert.schema.version = None
        with pytest.raises(pittgoogle.exceptions.SchemaError):
            alert.schema._name_in_bucket(alert=alert)
