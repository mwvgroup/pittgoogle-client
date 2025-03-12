# -*- coding: UTF-8 -*-
"""Fixtures for unit tests."""
import io
import json
from pathlib import Path

import fastavro
import pytest

import pittgoogle

import load_data


TESTS_DATA_DIR = Path(__file__).parent / "data"
SCHEMAS_DIR = pittgoogle.__package_path__ / "schemas"


# [FIXME]
# I'm fighting with pytest a lot over how to define the fixtures and parameterizations.
# Maybe I should be using unittest.
@pytest.fixture
def survey_names() -> list[str]:
    """List of all survey names supported by pittgoogle."""
    return ["lsst", "ztf", "lvk"]


# [FIXME] Move most of this to load_data?
def _get_sample_alert_paths(survey: str) -> list[Path]:
    """Return all paths under 'tests/data/' that look like sample alerts for `survey`."""
    alert_paths = [
        path
        for path in (TESTS_DATA_DIR / "sample_alerts" / survey).iterdir()
        if path.suffix in [".avro", ".json"]
    ]
    return alert_paths


@pytest.fixture
def sample_alerts_lsst() -> list[load_data.TestAlert]:
    """List of all LSST sample alerts."""
    survey = "lsst"
    alert_paths = _get_sample_alert_paths(survey)
    alerts = []
    for alert_path in alert_paths:
        # Expecting alert_path names like "lsst.v7_4.avro".
        schema_fname = alert_path.with_suffix(".alert.avsc").name
        schema_version = alert_path.suffixes[0].strip(".")
        major, minor = schema_version.strip("v").split("_")
        schema_path = SCHEMAS_DIR / survey / major / minor / schema_fname
        schema = fastavro.schema.load_schema(schema_path)
        alert_bytes = alert_path.read_bytes()
        bytes_io = io.BytesIO(alert_bytes[5:])
        alerts.append(
            load_data.TestAlert(
                survey=survey,
                schema_name=survey,
                schema_version=schema_version,
                path=alert_path,
                dict_=fastavro.schemaless_reader(bytes_io, schema),
            )
        )
    return alerts


@pytest.fixture
def random_alerts_lsst() -> list[load_data.TestAlert]:
    return [load_data.RandomLsst().to_testalert(), load_data.RandomLsst().to_minimal_testalert()]


@pytest.fixture
def sample_alerts_lvk() -> list[load_data.TestAlert]:
    survey = "lvk"
    alert_paths = [
        f for f in (TESTS_DATA_DIR / "sample_alerts" / survey).iterdir() if f.suffix == ".json"
    ]
    alerts = []
    for alert_path in alert_paths:
        alert_bytes = alert_path.read_bytes()
        alerts.append(
            load_data.TestAlert(
                survey=survey,
                schema_name=survey,
                schema_version="UNKNOWN",
                path=alert_path,
                dict_=json.loads(alert_bytes),
            )
        )
    return alerts


@pytest.fixture
def sample_alerts_ztf() -> list[load_data.TestAlert]:
    """List of all ZTF sample alerts."""
    survey = "ztf"
    alert_paths = _get_sample_alert_paths(survey)
    alerts = []
    for alert_path in alert_paths:
        alert_bytes = alert_path.read_bytes()
        alerts.append(
            load_data.TestAlert(
                survey=survey,
                schema_name=survey,
                schema_version=alert_path.suffixes[0].strip("."),
                path=alert_path,
                dict_=list(fastavro.reader(io.BytesIO(alert_bytes)))[0],
            )
        )
    return alerts


@pytest.fixture
def sample_alerts(
    sample_alerts_lsst, sample_alerts_lvk, sample_alerts_ztf
) -> list[load_data.TestAlert]:
    return [*sample_alerts_lsst, *sample_alerts_lvk, *sample_alerts_ztf]


@pytest.fixture
def sample_alert(sample_alerts_ztf) -> load_data.TestAlert:
    """Single sample alert. Useful when a test needs a sample alert but doesn't care which one."""
    return sample_alerts_ztf[0]
