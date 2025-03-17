# -*- coding: UTF-8 -*-
"""Unit tests for the registry module."""
import json

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
            serialized_dict = schema.serialize(sample_alert_dict, serializer="json")
            assert json.loads(serialized_dict) == sample_alert_dict


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
