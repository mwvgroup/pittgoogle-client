# -*- coding: UTF-8 -*-
"""Unit tests for the alert module."""
import base64
import datetime
import json

import astropy.table
import google.cloud.pubsub_v1
import pandas as pd

import pittgoogle


class TestAlertFrom:
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
            event, context, schema_name="default_schema"
        )
        assert isinstance(alert_instance, pittgoogle.Alert)
        assert alert_instance.schema_name == "default_schema"
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
        alert_instance = pittgoogle.Alert.from_cloud_run(envelope, schema_name="default_schema")
        assert isinstance(alert_instance, pittgoogle.Alert)
        assert alert_instance.schema_name == "default_schema"
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
        alert_instance = pittgoogle.Alert.from_msg(msg, schema_name="default_schema")
        assert isinstance(alert_instance, pittgoogle.Alert)
        assert alert_instance.schema_name == "default_schema"
        assert alert_instance.msg == msg


class TestAlertProperties:
    def test_skymap(self, sample_alerts_lvk):
        for sample_alert in sample_alerts_lvk:
            alert = pittgoogle.Alert.from_path(
                sample_alert.path, schema_name=sample_alert.schema_name
            )
            if "retraction" not in sample_alert.path.name:
                assert isinstance(alert.skymap, astropy.table.QTable)
            else:
                assert alert.skymap is None

    def test_dataframe(self, random_alerts_lsst, sample_alerts_lsst):
        # [FIXME] This is only testing schema "lsst.v7_4.alert"
        full, minimal = random_alerts_lsst

        mandatory_cols = set(full.pgalert.get("source").keys())
        all_cols = mandatory_cols.union(full.pgalert.get("prv_forced_sources")[0].keys())

        # Make sure we have some data that will test the bug from issue #76.
        assert minimal.pgalert.get("prv_sources") is None
        assert minimal.pgalert.get("prv_forced_sources") is None

        for testalert in random_alerts_lsst + sample_alerts_lsst:
            if testalert.schema_name != "lsst.v7_4.alert":
                continue
            pgdf = testalert.pgalert.dataframe
            assert isinstance(pgdf, pd.DataFrame)
            assert set(pgdf.columns) == mandatory_cols or set(pgdf.columns) == all_cols

    def test_name_in_bucket(self):
        alert_dict = {
            "diaObject": {"diaObjectId": 222},
            "diaSource": {"diaSourceId": 3333, "midpointMjdTai": 60745.0031},
        }
        alert = pittgoogle.Alert.from_msg(
            pittgoogle.types_.PubsubMessageLike(data=json.dumps(alert_dict))
        )
        alert.schema_name = "lsst"
        alert._schema = None
        alert.schema.version = "v7_4"
        alert.schema.deserialize = json.loads

        assert alert.name_in_bucket == "v7_4/2025-03-11/222/3333.avro"


class TestAlertMethods:
    def test_prep_for_publish(self, sample_alerts):
        for sample_alert in sample_alerts:
            alert = pittgoogle.Alert.from_path(
                sample_alert.path, schema_name=sample_alert.schema_name
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
