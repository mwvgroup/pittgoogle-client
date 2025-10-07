import random
from pathlib import Path

import attrs
import yaml

import pittgoogle

# Load the schema manifest as a list of dicts sorted by key.
manifest_yaml = pittgoogle.__package_path__ / "registry_manifests" / "schemas.yml"
SCHEMA_MANIFEST = yaml.safe_load(manifest_yaml.read_text())


@attrs.define(kw_only=True)
class TestAlert:
    """Container for a single sample alert."""

    schema_name: str | None = attrs.field(default=None)
    schema_version: str | None = attrs.field(default=None)
    survey: str | None = attrs.field(default=None)
    path: Path | None = attrs.field(default=None)
    bytes_: dict | None = attrs.field(default=None)
    dict_: dict | None = attrs.field(default=None)

    @property
    def pgalert(self) -> pittgoogle.Alert:
        if self.path:
            return pittgoogle.Alert.from_path(self.path, schema_name=self.schema_name)
        return pittgoogle.Alert.from_dict(
            self.dict_, attributes={"kafka.timestamp": 1757145492393}, schema_name=self.schema_name
        )


@attrs.define(kw_only=True)
class RandomLsst:
    """Generate random data using LSST schema."""

    def to_testalert(self) -> TestAlert:
        """Return an alert with non-null values for all fields."""
        return TestAlert(
            survey="lsst",
            schema_name="lsst",
            schema_version="v9_0",
            dict_={
                "diaSourceId": random.randint(1, 1000),
                "observation_reason": None,
                "target_name": None,
                "diaSource": self.dia_source(),
                "prvDiaSources": [self.dia_source() for _ in range(3)],
                "prvDiaForcedSources": [self.dia_forced_source() for _ in range(3)],
                "diaObject": self.dia_object(),
                "ssSource": self.ss_source(),
                "MBCORB": self.mbcorb(),
                "cutoutDifference": bytes(random.getrandbits(8) for _ in range(10)),
                "cutoutScience": bytes(random.getrandbits(8) for _ in range(10)),
                "cutoutTemplate": bytes(random.getrandbits(8) for _ in range(10)),
            },
        )

    def to_minimal_testalert(self) -> TestAlert:
        """Return an alert with `None` for all fields that are allowed to be null."""
        return TestAlert(
            survey="lsst",
            schema_name="lsst",
            schema_version="v9_0",
            dict_={
                "diaSourceId": random.randint(1, 1000),
                "observation_reason": None,
                "target_name": None,
                "diaSource": self.dia_source(),
                "prvDiaSources": None,
                "prvDiaForcedSources": None,
                "diaObject": self.dia_object(),
                "ssSource": self.ss_source(),
                "MBCORB": None,
                "cutoutDifference": None,
                "cutoutScience": None,
                "cutoutTemplate": None,
            },
        )

    @staticmethod
    def band() -> str:
        return random.choice(["u", "g", "r", "i", "z", "y"])

    @staticmethod
    def dia_object() -> dict:
        return {
            "diaObjectId": random.randint(10000, 20000),
            "validityStartMjdTai": random.uniform(60900, 62000),
            "ra": random.uniform(0, 360),
            "raErr": random.uniform(0, 1),
            "dec": random.uniform(-90, 90),
            "decErr": random.uniform(0, 1),
            "ra_dec_Cov": random.uniform(-0.1, 0.1),
            "u_psfFluxMean": random.uniform(10, 1000),
            "u_psfFluxMeanErr": random.uniform(0, 10),
            "u_psfFluxSigma": random.uniform(0, 20),
            "u_psfFluxNdata": random.randint(5, 50),
            "u_fpFluxMean": random.uniform(10, 1000),
            "u_fpFluxMeanErr": random.uniform(0, 10),
            "g_psfFluxMean": random.uniform(10, 1000),
            "g_psfFluxMeanErr": random.uniform(0, 10),
            "g_psfFluxSigma": random.uniform(0, 20),
            "g_psfFluxNdata": random.randint(5, 50),
            "g_fpFluxMean": random.uniform(10, 1000),
            "g_fpFluxMeanErr": random.uniform(0, 10),
            "r_psfFluxMean": random.uniform(10, 1000),
            "r_psfFluxMeanErr": random.uniform(0, 10),
            "r_psfFluxSigma": random.uniform(0, 20),
            "r_psfFluxNdata": random.randint(5, 50),
            "r_fpFluxMean": random.uniform(10, 1000),
            "r_fpFluxMeanErr": random.uniform(0, 10),
            "i_psfFluxMean": random.uniform(10, 1000),
            "i_psfFluxMeanErr": random.uniform(0, 10),
            "i_psfFluxSigma": random.uniform(0, 20),
            "i_psfFluxNdata": random.randint(5, 50),
            "i_fpFluxMean": random.uniform(10, 1000),
            "i_fpFluxMeanErr": random.uniform(0, 10),
            "z_psfFluxMean": random.uniform(10, 1000),
            "z_psfFluxMeanErr": random.uniform(0, 10),
            "z_psfFluxSigma": random.uniform(0, 20),
            "z_psfFluxNdata": random.randint(5, 50),
            "z_fpFluxMean": random.uniform(10, 1000),
            "z_fpFluxMeanErr": random.uniform(0, 10),
            "y_psfFluxMean": random.uniform(10, 1000),
            "y_psfFluxMeanErr": random.uniform(0, 10),
            "y_psfFluxSigma": random.uniform(0, 20),
            "y_psfFluxNdata": random.randint(5, 50),
            "y_fpFluxMean": random.uniform(10, 1000),
            "y_fpFluxMeanErr": random.uniform(0, 10),
            "u_scienceFluxMean": random.uniform(10, 1000),
            "u_scienceFluxMeanErr": random.uniform(0, 10),
            "g_scienceFluxMean": random.uniform(10, 1000),
            "g_scienceFluxMeanErr": random.uniform(0, 10),
            "r_scienceFluxMean": random.uniform(10, 1000),
            "r_scienceFluxMeanErr": random.uniform(0, 10),
            "i_scienceFluxMean": random.uniform(10, 1000),
            "i_scienceFluxMeanErr": random.uniform(0, 10),
            "z_scienceFluxMean": random.uniform(10, 1000),
            "z_scienceFluxMeanErr": random.uniform(0, 10),
            "y_scienceFluxMean": random.uniform(10, 1000),
            "y_scienceFluxMeanErr": random.uniform(0, 10),
            "u_psfFluxMin": random.uniform(0, 1000),
            "u_psfFluxMax": random.uniform(0, 1000),
            "u_psfFluxMaxSlope": random.uniform(0, 1000),
            "u_psfFluxErrMean": random.uniform(0, 10),
            "g_psfFluxMin": random.uniform(0, 1000),
            "g_psfFluxMax": random.uniform(0, 1000),
            "g_psfFluxMaxSlope": random.uniform(0, 1000),
            "g_psfFluxErrMean": random.uniform(0, 10),
            "r_psfFluxMin": random.uniform(0, 1000),
            "r_psfFluxMax": random.uniform(0, 1000),
            "r_psfFluxMaxSlope": random.uniform(0, 1000),
            "r_psfFluxErrMean": random.uniform(0, 10),
            "i_psfFluxMin": random.uniform(0, 1000),
            "i_psfFluxMax": random.uniform(0, 1000),
            "i_psfFluxMaxSlope": random.uniform(0, 1000),
            "i_psfFluxErrMean": random.uniform(0, 10),
            "z_psfFluxMin": random.uniform(0, 1000),
            "z_psfFluxMax": random.uniform(0, 1000),
            "z_psfFluxMaxSlope": random.uniform(0, 1000),
            "z_psfFluxErrMean": random.uniform(0, 10),
            "y_psfFluxMin": random.uniform(0, 1000),
            "y_psfFluxMax": random.uniform(0, 1000),
            "y_psfFluxMaxSlope": random.uniform(0, 1000),
            "y_psfFluxErrMean": random.uniform(0, 10),
            "firstDiaSourceMjdTai": random.uniform(61000, 62000),
            "lastDiaSourceMjdTai": random.uniform(61000, 62000),
            "nDiaSources": random.randint(1, 100),
        }

    @staticmethod
    def dia_source() -> dict:
        return {
            "diaSourceId": random.randint(1, 1000),
            "visit": random.randint(100000, 200000),
            "detector": random.randint(1, 189),
            "diaObjectId": random.randint(10000, 20000),
            "ssObjectId": random.randint(30000, 40000),
            "parentDiaSourceId": random.randint(50000, 60000),
            "midpointMjdTai": random.uniform(58000, 60000),
            "ra": random.uniform(0, 360),
            "raErr": random.uniform(0, 0.1),
            "dec": random.uniform(-90, 90),
            "decErr": random.uniform(0, 0.1),
            "ra_dec_Cov": random.uniform(-0.01, 0.01),
            "x": random.uniform(0, 4000),
            "xErr": random.uniform(0, 1),
            "y": random.uniform(0, 4000),
            "yErr": random.uniform(0, 1),
            "centroid_flag": random.choice([True, False]),
            "apFlux": random.uniform(0, 1000),
            "apFluxErr": random.uniform(0, 10),
            "apFlux_flag": random.choice([True, False]),
            "apFlux_flag_apertureTruncated": random.choice([True, False]),
            "isNegative": random.choice([True, False]),
            "snr": random.uniform(0, 100),
            "psfFlux": random.uniform(0, 1000),
            "psfFluxErr": random.uniform(0, 10),
            "psfLnL": random.uniform(-1000, 0),
            "psfChi2": random.uniform(0, 1000),
            "psfNdata": random.randint(1, 100),
            "psfFlux_flag": random.choice([True, False]),
            "psfFlux_flag_edge": random.choice([True, False]),
            "psfFlux_flag_noGoodPixels": random.choice([True, False]),
            "trailFlux": random.uniform(0, 1000),
            "trailFluxErr": random.uniform(0, 10),
            "trailRa": random.uniform(0, 360),
            "trailRaErr": random.uniform(0, 0.1),
            "trailDec": random.uniform(-90, 90),
            "trailDecErr": random.uniform(0, 0.1),
            "trailLength": random.uniform(0, 10),
            "trailLengthErr": random.uniform(0, 1),
            "trailAngle": random.uniform(0, 360),
            "trailAngleErr": random.uniform(0, 10),
            "trailChi2": random.uniform(0, 1000),
            "trailNdata": random.randint(1, 100),
            "trail_flag_edge": random.choice([True, False]),
            "dipoleMeanFlux": random.uniform(0, 1000),
            "dipoleMeanFluxErr": random.uniform(0, 10),
            "dipoleFluxDiff": random.uniform(-100, 100),
            "dipoleFluxDiffErr": random.uniform(0, 10),
            "dipoleLength": random.uniform(0, 10),
            "dipoleAngle": random.uniform(0, 360),
            "dipoleChi2": random.uniform(0, 1000),
            "dipoleNdata": random.randint(1, 100),
            "scienceFlux": random.uniform(0, 1000),
            "scienceFluxErr": random.uniform(0, 10),
            "forced_PsfFlux_flag": random.choice([True, False]),
            "forced_PsfFlux_flag_edge": random.choice([True, False]),
            "forced_PsfFlux_flag_noGoodPixels": random.choice([True, False]),
            "templateFlux": random.uniform(0, 1000),
            "templateFluxErr": random.uniform(0, 10),
            "ixx": random.uniform(0, 100),
            "iyy": random.uniform(-100, 100),
            "ixy": random.uniform(-100, 100),
            "ixxPSF": random.uniform(0, 100),
            "iyyPSF": random.uniform(0, 100),
            "ixyPSF": random.uniform(-50, 50),
            "shape_flag": random.choice([True, False]),
            "shape_flag_no_pixels": random.choice([True, False]),
            "shape_flag_not_contained": random.choice([True, False]),
            "shape_flag_parent_source": random.choice([True, False]),
            "extendedness": random.uniform(0, 1),
            "reliability": random.uniform(0, 1),
            "band": RandomLsst.band,
            "isDipole": random.choice([True, False]),
            "dipoleFitAttempted": random.choice([True, False]),
            "timeProcessedMjdTai": random.uniform(58000, 60000),
            "timeWithdrawnMjdTai": random.uniform(58000, 60000),
            "bboxSize": random.randint(1, 200),
            "pixelFlags": random.choice([True, False]),
            "pixelFlags_bad": random.choice([True, False]),
            "pixelFlags_cr": random.choice([True, False]),
            "pixelFlags_crCenter": random.choice([True, False]),
            "pixelFlags_edge": random.choice([True, False]),
            "pixelFlags_nodata": random.choice([True, False]),
            "pixelFlags_nodataCenter": random.choice([True, False]),
            "pixelFlags_interpolated": random.choice([True, False]),
            "pixelFlags_interpolatedCenter": random.choice([True, False]),
            "pixelFlags_offimage": random.choice([True, False]),
            "pixelFlags_saturated": random.choice([True, False]),
            "pixelFlags_saturatedCenter": random.choice([True, False]),
            "pixelFlags_suspect": random.choice([True, False]),
            "pixelFlags_suspectCenter": random.choice([True, False]),
            "pixelFlags_streak": random.choice([True, False]),
            "pixelFlags_streakCenter": random.choice([True, False]),
            "pixelFlags_injected": random.choice([True, False]),
            "pixelFlags_injectedCenter": random.choice([True, False]),
            "pixelFlags_injected_template": random.choice([True, False]),
            "pixelFlags_injected_templateCenter": random.choice([True, False]),
            "glint_trail": random.choice([True, False]),
        }

    @staticmethod
    def dia_forced_source() -> dict:
        return {
            "diaForcedSourceId": random.randint(100000, 200000),
            "diaObjectId": random.randint(10000, 20000),
            "ra": random.uniform(0, 360),
            "dec": random.uniform(-90, 90),
            "visit": random.randint(1000, 5000),
            "detector": random.randint(1, 189),
            "psfFlux": random.uniform(10, 1000),
            "psfFluxErr": random.uniform(0, 10),
            "midpointMjdTai": random.uniform(58000, 60000),
            "scienceFlux": random.uniform(10, 1000),
            "scienceFluxErr": random.uniform(0, 10),
            "band": RandomLsst.band,
            "timeProcessedMjdTai": random.uniform(58000, 60000),
            "timeWithdrawnMjdTai": random.uniform(58000, 60000),
        }

    @staticmethod
    def ss_source() -> dict:
        return {
            "ssObjectId": random.randint(1, 1000),
            "diaSourceId": random.randint(1, 1000),
            "eclipticLambda": random.uniform(0, 360),
            "eclipticBeta": random.uniform(-90, 90),
            "galacticL": random.uniform(0, 360),
            "galacticB": random.uniform(-90, 90),
            "phaseAngle": random.uniform(0, 180),
            "heliocentricDist": random.uniform(0, 100),
            "topocentricDist": random.uniform(0, 100),
            "predictedVMagnitude": random.uniform(0, 30),
            "residualRa": random.uniform(-1, 1),
            "residualDec": random.uniform(-1, 1),
            "heliocentricX": random.uniform(-100, 100),
            "heliocentricY": random.uniform(-100, 100),
            "heliocentricZ": random.uniform(-100, 100),
            "heliocentricVX": random.uniform(-100, 100),
            "heliocentricVY": random.uniform(-100, 100),
            "heliocentricVZ": random.uniform(-100, 100),
            "topocentricX": random.uniform(-100, 100),
            "topocentricY": random.uniform(-100, 100),
            "topocentricZ": random.uniform(-100, 100),
            "topocentricVX": random.uniform(-100, 100),
            "topocentricVY": random.uniform(-100, 100),
            "topocentricVZ": random.uniform(-100, 100),
        }

    @staticmethod
    def mbcorb() -> dict:
        return {
            "mpcDesignation": None,
            "ssObjectId": random.randint(10000, 20000),
            "mpcH": random.uniform(0, 30),
            "epoch": random.uniform(58000, 60000),
            "M": random.uniform(0, 360),
            "peri": random.uniform(0, 360),
            "node": random.uniform(0, 360),
            "incl": random.uniform(0, 180),
            "e": random.uniform(0, 1),
            "a": random.uniform(0, 100),
            "q": random.uniform(0, 100),
            "t_p": random.uniform(58000, 60000),
        }
