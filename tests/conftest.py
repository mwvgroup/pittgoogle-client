# -*- coding: UTF-8 -*-
"""Fixtures for unit tests."""
import io
from pathlib import Path

import attrs
import fastavro
import pytest

import pittgoogle

TESTS_DATA_DIR = Path(__file__).parent / "data"
SCHEMAS_DIR = pittgoogle.__package_path__ / "schemas"


@attrs.define(kw_only=True)
class SampleAlert:
    path: Path = attrs.field()
    dict_: dict = attrs.field()
    schema_name: str = attrs.field()
    schema_version: str = attrs.field()
    survey: str = attrs.field()


# @attrs.define(kw_only=True)
# class SurveyAlerts:
#     _sample_alerts: tuple[SampleAlert] = attrs.field(converter=tuple)

#     def __iter__(self):
#         return iter(self._sample_alerts)

#     def __getitem__(self, index):
#         return self._sample_alerts[index]

#     def __len__(self):
#         return len(self._sample_alerts)

#     def paths(self):
#         return [alert.path for alert in self._sample_alerts]

#     def dicts(self):
#         return [alert.dict_ for alert in self._sample_alerts]


@pytest.fixture
def sample_alerts_lsst() -> list[SampleAlert]:
    survey = "lsst"
    alert_paths = list((TESTS_DATA_DIR / "sample_alerts" / survey).iterdir())
    alerts = []
    for alert_path in alert_paths:
        schema_fname = alert_path.with_suffix(".alert.avsc").name
        schema_version = alert_path.suffixes[0].strip(".")
        _version = schema_version.strip("v").split("_")
        schema_path = SCHEMAS_DIR / survey / _version[0] / _version[1] / schema_fname
        schema = fastavro.schema.load_schema(schema_path)
        alert_bytes = alert_path.read_bytes()
        bytes_io = io.BytesIO(alert_bytes[5:])
        # bytes_io = io.BytesIO(alert_path.read_bytes()[5:])
        alerts.append(
            SampleAlert(
                survey=survey,
                schema_name=schema_fname.removesuffix(".avsc"),
                schema_version=schema_version,
                path=alert_path,
                dict_=fastavro.schemaless_reader(bytes_io, schema),
            )
        )
    return alerts


@pytest.fixture
def sample_alerts_ztf() -> list[SampleAlert]:
    survey = "ztf"
    alert_paths = list((TESTS_DATA_DIR / "sample_alerts" / survey).iterdir())
    alerts = []
    for alert_path in alert_paths:
        alert_bytes = alert_path.read_bytes()
        alerts.append(
            SampleAlert(
                survey=survey,
                schema_name=survey,
                schema_version=alert_path.suffixes[0].strip("."),
                path=alert_path,
                dict_=list(fastavro.reader(io.BytesIO(alert_bytes)))[0],
            )
        )
    return alerts


@pytest.fixture
def sample_alerts(sample_alerts_lsst, sample_alerts_ztf) -> list[SampleAlert]:
    return [*sample_alerts_lsst, *sample_alerts_ztf]


@pytest.fixture
def sample_alert(sample_alerts_ztf) -> SampleAlert:
    return sample_alerts_ztf[0]
