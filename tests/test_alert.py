# -*- coding: UTF-8 -*-
"""Unit tests for the alert module."""
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
            assert alert.attributes == {}
