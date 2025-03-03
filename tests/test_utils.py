# -*- coding: UTF-8 -*-
"""Unit tests for the utils module."""
import base64
import io
import json

import astropy.table
import fastavro

from pittgoogle.utils import Cast


class TestCast:
    def test_bytes_to_b64utf8(self):
        bytes_data = b"test data"
        expected_result = base64.b64encode(bytes_data).decode("utf-8")
        result = Cast.bytes_to_b64utf8(bytes_data)
        assert result == expected_result

    def test_json_to_dict(self):
        bytes_data = b'{"key": "value"}'
        expected_result = {"key": "value"}
        result = Cast.json_to_dict(bytes_data)
        assert result == expected_result

    def test_b64json_to_dict(self):
        dict_data = {"key": "value"}
        bytes_data = base64.b64encode(json.dumps(dict_data).encode("utf-8"))
        expected_result = dict_data
        result = Cast.b64json_to_dict(bytes_data)
        assert result == expected_result

    def test_avro_to_dict(self):
        schema = {"type": "record", "name": "Test", "fields": [{"name": "key", "type": "string"}]}
        dict_data = {"key": "value"}
        bytes_io = io.BytesIO()
        fastavro.writer(bytes_io, schema, [dict_data])
        bytes_data = bytes_io.getvalue()
        result = Cast.avro_to_dict(bytes_data)
        assert result == dict_data

    def test_b64avro_to_dict(self):
        schema = {"type": "record", "name": "Test", "fields": [{"name": "key", "type": "string"}]}
        dict_data = {"key": "value"}
        bytes_io = io.BytesIO()
        fastavro.writer(bytes_io, schema, [dict_data])
        bytes_data = base64.b64encode(bytes_io.getvalue())
        result = Cast.b64avro_to_dict(bytes_data)
        assert result == dict_data

    def test_alert_dict_to_table(self):
        alert_dict = {
            "objectId": "ZTF18abcd1234",
            "candidate": {"key1": "value1", "key2": "value2"},
            "prv_candidates": [{"key1": "value3", "key2": "value4"}],
        }
        table = Cast.alert_dict_to_table(alert_dict)
        assert isinstance(table, astropy.table.Table)
        assert table.meta["comments"] == "ZTF objectId: ZTF18abcd1234"
        assert len(table) == 2
        assert table["key1"][0] == "value1"
        assert table["key1"][1] == "value3"

    def test_strip_cutouts_ztf(self):
        alert_dict = {
            "key1": "value1",
            "cutoutScience": "cutout1",
            "cutoutTemplate": "cutout2",
            "cutoutDifference": "cutout3",
        }
        expected_result = {"key1": "value1"}
        result = Cast._strip_cutouts_ztf(alert_dict)
        assert result == expected_result

    def test_jd_to_readable_date(self):
        jd = 2451545.0  # Julian date for 2000-01-01 12:00:00
        expected_result = "01 Jan 2000 - 12:00:00"
        result = Cast.jd_to_readable_date(jd)
        assert result == expected_result
