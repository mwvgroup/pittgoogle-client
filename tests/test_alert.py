# -*- coding: UTF-8 -*-
"""Unit tests for the alert module."""
import base64
import datetime

import astropy.table
import google.cloud.pubsub_v1

import pittgoogle


class TestAlert:
    def test_from_path(self, sample_alerts):
        for sample_alert in sample_alerts:
            alert = pittgoogle.Alert.from_path(
                sample_alert.path, schema_name=sample_alert.schema_name
            )
            assert isinstance(alert, pittgoogle.Alert)
            assert alert.path == sample_alert.path
            assert alert.dict == sample_alert.dict_

    def test_from_dict(self, sample_alerts):
        for sample_alert in sample_alerts:
            alert = pittgoogle.Alert.from_dict(
                sample_alert.dict_, schema_name=sample_alert.schema_name
            )
            assert isinstance(alert, pittgoogle.Alert)
            assert alert.dict == sample_alert.dict_

            # alertid, objectid, and sourceid should have been added as attributes.
            key_gen = (alert.get_key(key) for key in ["alertid", "objectid", "sourceid"])
            _expected_keys = [".".join(key) if isinstance(key, list) else key for key in key_gen]
            expected_keys = set(key for key in _expected_keys if key)  # get rid of None
            assert set(alert.attributes) == expected_keys

    def test_from_cloud_functions(self, sample_alert):
        event, context = pittgoogle.Alert.from_path(
            sample_alert.path, schema_name=sample_alert.schema_name
        ).to_mock_input(cloud_functions=True)
        alert_instance = pittgoogle.Alert.from_cloud_functions(
            event, context, schema_name="test_schema"
        )
        assert isinstance(alert_instance, pittgoogle.Alert)
        assert alert_instance.schema_name == "test_schema"
        assert alert_instance.msg.data == base64.b64decode(event["data"])
        assert alert_instance.msg.attributes == event["attributes"]
        assert alert_instance.msg.message_id == context.event_id
        assert alert_instance.msg.publish_time == pittgoogle.Alert._str_to_datetime(
            context.timestamp
        )

    def test_from_cloud_run(self):
        envelope = {
            "message": {
                "data": base64.b64encode(b"test_data").decode("utf-8"),
                "attributes": {"key": "value"},
                "message_id": "12345",
                "publish_time": "2023-01-01T00:00:00Z",
                "ordering_key": "order_key",
            }
        }
        alert_instance = pittgoogle.Alert.from_cloud_run(envelope, schema_name="test_schema")
        assert isinstance(alert_instance, pittgoogle.Alert)
        assert alert_instance.schema_name == "test_schema"
        assert alert_instance.msg.data == base64.b64decode(
            envelope["message"]["data"].encode("utf-8")
        )
        assert alert_instance.msg.attributes == envelope["message"]["attributes"]
        assert alert_instance.msg.message_id == envelope["message"]["message_id"]
        assert alert_instance.msg.publish_time == pittgoogle.Alert._str_to_datetime(
            envelope["message"]["publish_time"]
        )
        assert alert_instance.msg.ordering_key == envelope["message"]["ordering_key"]

    def test_from_msg(self):
        msg = google.cloud.pubsub_v1.types.PubsubMessage(
            data=b"test_data",
            attributes={"key": "value"},
            message_id="12345",
            publish_time=datetime.datetime(2023, 1, 1, 0, 0, 0, tzinfo=datetime.timezone.utc),
        )
        alert_instance = pittgoogle.Alert.from_msg(msg, schema_name="test_schema")
        assert isinstance(alert_instance, pittgoogle.Alert)
        assert alert_instance.schema_name == "test_schema"
        assert alert_instance.msg == msg

    def test_skymap(self, sample_alerts_lvk):
        for sample_alert in sample_alerts_lvk:
            alert = pittgoogle.Alert.from_path(
                sample_alert.path, schema_name=sample_alert.schema_name
            )
            if "retraction" not in sample_alert.path.name:
                assert isinstance(alert.skymap, astropy.table.QTable)
            else:
                assert alert.skymap is None

    def test_prep_for_publish(self, sample_alerts):
        for sample_alert in sample_alerts:
            alert = pittgoogle.Alert.from_dict(
                sample_alert.dict_, schema_name=sample_alert.schema_name
            )
            message, attributes = alert._prep_for_publish()
            assert isinstance(message, bytes)
            assert isinstance(attributes, dict)
            assert all(isinstance(k, str) and isinstance(v, str) for k, v in attributes.items())

    def test_str_to_datetime(self):
        str_time = "2023-01-01T00:00:00.000000Z"
        dt = pittgoogle.Alert._str_to_datetime(str_time)
        assert dt == datetime.datetime(2023, 1, 1, 0, 0, 0, tzinfo=datetime.timezone.utc)

        str_time = "2023-01-01T00:00:00Z"
        dt = pittgoogle.Alert._str_to_datetime(str_time)
        assert dt == datetime.datetime(2023, 1, 1, 0, 0, 0, tzinfo=datetime.timezone.utc)
