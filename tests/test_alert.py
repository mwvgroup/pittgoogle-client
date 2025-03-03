# -*- coding: UTF-8 -*-
"""Unit tests for the alert module."""
import astropy.table

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

    def test_skymap(self, sample_alerts_lvk):
        for sample_alert in sample_alerts_lvk:
            alert = pittgoogle.Alert.from_path(
                sample_alert.path, schema_name=sample_alert.schema_name
            )
            if "retraction" not in sample_alert.path.name:
                assert isinstance(alert.skymap, astropy.table.QTable)
            else:
                assert alert.skymap is None
