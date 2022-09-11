#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

"""Functions to support working with alerts and related data."""


from base64 import b64decode, b64encode
from collections import OrderedDict
import inspect
from io import BytesIO
import json
import logging
from typing import ClassVar

from astropy.table import Table
from astropy.time import Time
import attrs
import fastavro
import pandas as pd

LOGGER = logging.getLogger(__name__)


# --- Other
@attrs.define
class PittGoogleProjectIds:
    """Pitt-Google broker's Google Cloud project IDs."""

    production: ClassVar[str] = "ardent-cycling-243415"
    """Production project."""
    testing: ClassVar[str] = "avid-heading-329016"
    """Testing project."""
    billing: ClassVar[str] = "light-cycle-328823"
    """Billing project."""


class Cast:
    """Methods to convert data types."""

    @staticmethod
    def bytes_to_b64utf8(bytes_data):
        """Convert bytes data to UTF-8.

        Parameters
        -----------
        bytes_data : `bytes`
            Data to be converted to UTF-8.

        Returns
        -----------
        data : `dict`
            ``bytes_data`` converted to a string in UTF-8 format
        """
        if bytes_data is not None:
            return b64encode(bytes_data).decode("utf-8")

    @staticmethod
    def base64_to_dict(bytes_data):
        """Convert base64 encoded bytes data to a dict.

        Parameters
        -----------
        bytes_data : `Base64`
            Data to be converted to a dictionary.

        Returns:
        data : `dict`
            ``bytes_data`` unpacked into a dictionary.
        """
        if bytes_data is not None:
            return json.loads(b64decode(bytes_data).decode("utf-8"))

    @staticmethod
    def avro_to_dict(bytes_data):
        """Convert Avro serialized bytes data to a dict.

        Parameters
        ------------
        bytes_data : `bytes`
            Avro serialized bytes data to be converted to a dictionary

        Returns
        --------
        data : `dict`
            ``bytes_data`` unpacked into a dictionary.
        """
        if bytes_data is not None:
            with BytesIO(bytes_data) as fin:
                alert_dicts = [r for r in fastavro.reader(fin)]  # list with single dict
            return alert_dicts[0]

    @staticmethod
    def b64avro_to_dict(bytes_data):
        """Convert base64 encoded, Avro serialized bytes data to a dict.

        Parameters
        -----------
        bytes_data : `bytes`:
            base64 encoded, Avro serialized bytes to be converted to a dictionary

        Returns
        ---------
        data : `dict`
            ``bytes_data`` unpacked into a dictionary.
        """
        # if bytes_data is not None:
        #     with BytesIO(b64decode(bytes_data)) as fin:
        #         alert_dicts = [r for r in fastavro.reader(fin)]
        # list with single dict
        #     return alert_dicts[0]
        return Cast.avro_to_dict(b64decode(bytes_data))

    # --- Work with alert dictionaries
    @staticmethod
    def alert_dict_to_dataframe(alert_dict: dict) -> pd.DataFrame:
        """Package a ZTF alert dictionary into a dataframe.

        Adapted from:
        https://github.com/ZwickyTransientFacility/ztf-avro-alert/blob/master/notebooks/Filtering_alerts.ipynb
        """
        dfc = pd.DataFrame(alert_dict["candidate"], index=[0])
        df_prv = pd.DataFrame(alert_dict["prv_candidates"])
        df = pd.concat([dfc, df_prv], ignore_index=True, sort=True)
        df = df[dfc.columns]  # return to original column ordering

        # we'll attach some metadata
        # note this may not be preserved after all operations
        # https://stackoverflow.com/questions/14688306/adding-meta-information-metadata-to-pandas-dataframe
        df.objectId = alert_dict["objectId"]
        return df

    @staticmethod
    def alert_dict_to_table(alert_dict: dict) -> Table:
        """Package a ZTF alert dictionary into an Astopy Table."""
        # collect rows for the table
        candidate = OrderedDict(alert_dict["candidate"])
        rows = [candidate]
        for prv_cand in alert_dict["prv_candidates"]:
            # astropy 3.2.1 cannot handle dicts with different keys (fixed by 4.1)
            prv_cand_tmp = {key: prv_cand.get(key, None) for key in candidate.keys()}
            rows.append(prv_cand_tmp)

        # create and return the table
        table = Table(rows=rows)
        table.meta["comments"] = f"ZTF objectId: {alert_dict['objectId']}"
        return table

    @staticmethod
    def _strip_cutouts_ztf(alert_dict: dict) -> dict:
        """Drop the cutouts from the alert dictionary.

        Args:
            alert_dict: ZTF alert formated as a dict
        Returns:
            `alert_data` with the cutouts (postage stamps) removed
        """
        cutouts = ["cutoutScience", "cutoutTemplate", "cutoutDifference"]
        alert_stripped = {k: v for k, v in alert_dict.items() if k not in cutouts}
        return alert_stripped

    # dates
    @staticmethod
    def jd_to_readable_date(jd):
        """Convert a Julian date to a human readable string.

        Parameters
        -----------
        jd : `float`
            Datetime value in julian format

        Returns
        --------
        date : `str`
            ``jd`` in the format 'day mon year hour:min'
        """
        return Time(jd, format="jd").strftime("%d %b %Y - %H:%M:%S")


# def init_defaults(obj):
#     """Return dictionary of default values for args of obj.__init__."""
#     params = inspect.signature(obj.__init__).parameters
#     # ClassDefaults = namedtuple(
#     #     "ClassDefaults", " ".join(name for name in params.keys())
#     # )
#     # return ClassDefaults._make(params[key].default for key in ClassDefaults._fields)
#     return dict((name, params[name].default) for name in params.keys())


# --- Survey-specific
def ztf_fid_names() -> dict:
    """Return a dictionary mapping the ZTF `fid` (filter ID) to the common name."""
    return {1: "g", 2: "r", 3: "i"}
