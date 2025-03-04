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
    """Container for a single sample alert."""

    path: Path = attrs.field()
    dict_: dict = attrs.field()
    schema_name: str = attrs.field()
    schema_version: str = attrs.field()
    survey: str = attrs.field()


def _get_sample_alert_paths(survey: str) -> list[Path]:
    """Return all paths under 'tests/data/' that look like sample alerts for `survey`."""
    alert_paths = [
        path
        for path in (TESTS_DATA_DIR / "sample_alerts" / survey).iterdir()
        if path.suffix in [".avro", ".json"]
    ]
    return alert_paths


@pytest.fixture
def sample_alerts_lsst() -> list[SampleAlert]:
    """List of all LSST sample alerts."""
    survey = "lsst"
    alert_paths = _get_sample_alert_paths(survey)
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
    """List of all ZTF sample alerts."""
    survey = "ztf"
    alert_paths = _get_sample_alert_paths(survey)
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
    """List of all sample alerts for all surveys."""
    return [*sample_alerts_lsst, *sample_alerts_ztf]


@pytest.fixture
def sample_alert(sample_alerts_ztf) -> SampleAlert:
    """Single sample alert. Useful when a test needs a sample alert but doesn't care which one."""
    return sample_alerts_ztf[0]
