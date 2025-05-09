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

    def test_from_dict(self, sample_alerts, random_alerts):
        for test_alert in sample_alerts + random_alerts:
            alert = pittgoogle.Alert.from_dict(
                test_alert.dict_, schema_name=test_alert.schema_name
            )
            assert isinstance(alert, pittgoogle.Alert)
            assert alert.dict == test_alert.dict_

    def test_attributes(self, sample_alerts, random_alerts):
        for test_alert in sample_alerts + random_alerts:
            alert = pittgoogle.Alert.from_dict(
                test_alert.dict_, schema_name=test_alert.schema_name
            )
            # We expect that the following keys were added to alert.attributes.
            #  to  alertid, objectid, sourceid, ssobjectid, and schema version should have been added as attributes.
            _id_keys = (
                alert.get_key(key) for key in ["alertid", "objectid", "sourceid", "ssobjectid"]
            )
            id_keys = ["_".join(key) if isinstance(key, list) else key for key in _id_keys]
            index_keys = ["healpix9", "healpix19", "healpix29"]
            metadata_keys = ["schema_version", "n_previous_detections"]
            # 'if key' to drop None.
            expected_keys = set(key for key in id_keys + index_keys + metadata_keys if key)
            assert set(alert.attributes) == expected_keys

    def test_from_cloud_functions(self, sample_alert):
        event, context = pittgoogle.Alert.from_path(
            sample_alert.path, schema_name=sample_alert.schema_name
        ).to_mock_input(cloud_functions=True)
        alert_instance = pittgoogle.Alert.from_cloud_functions(
            event, context, schema_name="default"
        )
        assert isinstance(alert_instance, pittgoogle.Alert)
        assert alert_instance.schema_name == "default"
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
        alert_instance = pittgoogle.Alert.from_cloud_run(envelope, schema_name="default")
        assert isinstance(alert_instance, pittgoogle.Alert)
        assert alert_instance.schema_name == "default"
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
        alert_instance = pittgoogle.Alert.from_msg(msg, schema_name="default")
        assert isinstance(alert_instance, pittgoogle.Alert)
        assert alert_instance.schema_name == "default"
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

    def test_dataframe(self, random_alerts_lsst, sample_alert_lsst_latest):
        # [FIXME] Only testing the latest LSST schema version for now.

        full, minimal = random_alerts_lsst

        mandatory_cols = set(full.pgalert.get("source").keys())
        all_cols = mandatory_cols.union(full.pgalert.get("prv_forced_sources")[0].keys())

        # Make sure we have some data that will test the bug from issue #76.
        assert minimal.pgalert.get("prv_sources") is None
        assert minimal.pgalert.get("prv_forced_sources") is None

        for testalert in random_alerts_lsst + [sample_alert_lsst_latest]:
            pgdf = testalert.pgalert.dataframe
            assert isinstance(pgdf, pd.DataFrame)
            assert set(pgdf.columns) == mandatory_cols or set(pgdf.columns) == all_cols

    def test_healpix(self):
        alert_dict = {"ra": 270.1, "dec": -30.2}
        alert = pittgoogle.Alert.from_dict(alert_dict, schema_name="default")
        assert alert.healpix9 == 1_839_101
        assert alert.healpix19 == 1_928_437_384_743
        assert alert.healpix29 == 2_022_113_159_144_974_258

    def test_name_in_bucket(self):
        alert_dict = {
            "diaObject": {"diaObjectId": 222},
            "diaSource": {"diaSourceId": 3333, "midpointMjdTai": 60745.0031},
        }
        alert = pittgoogle.Alert.from_dict(alert_dict, "lsst")
        alert.schema_name = "lsst"
        alert.schema.version = "v7_4"
        assert alert.name_in_bucket == "v7_4/2025-03-11/222/3333.avro"

    def test_get_wrappers(self):
        alert_dict = {
            "alertid": 12345,
            "objectid": 67890,
            "sourceid": 1234567890,
            "ra": 270.0123456789,
            "dec": -32.0123456789,
        }
        alert = pittgoogle.Alert.from_msg(
            pittgoogle.types_.PubsubMessageLike(data=json.dumps(alert_dict).encode("utf-8")),
            "default",
        )
        assert alert.alertid == 12345
        assert alert.objectid == 67890
        assert alert.sourceid == 1234567890
        assert alert.ra == 270.0123456789
        assert alert.dec == -32.0123456789


class TestAlertMethods:
    def test_str_to_datetime(self):
        str_time = "2023-01-01T00:00:00.000000Z"
        dt = pittgoogle.Alert._str_to_datetime(str_time)
        assert dt == datetime.datetime(2023, 1, 1, 0, 0, 0, tzinfo=datetime.timezone.utc)

        str_time = "2023-01-01T00:00:00Z"
        dt = pittgoogle.Alert._str_to_datetime(str_time)
        assert dt == datetime.datetime(2023, 1, 1, 0, 0, 0, tzinfo=datetime.timezone.utc)
