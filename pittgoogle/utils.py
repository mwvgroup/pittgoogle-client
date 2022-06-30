#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

"""Functions to support working with alerts and related data."""


import logging
from astropy.table import Table
from collections import OrderedDict, namedtuple
import inspect
import pandas as pd
from base64 import b64decode, b64encode
import fastavro
from io import BytesIO
import json
from astropy.time import Time
import os


LOGGER = logging.getLogger(__name__)


# --- Survey-specific
def ztf_fid_names() -> dict:
    """Return a dictionary mapping the ZTF `fid` (filter ID) to the common name."""
    return {1: "g", 2: "r", 3: "i"}


# --- Work with alert dictionaries
def alert_dict_to_dataframe(alert_dict: dict) -> pd.DataFrame:
    """Package a ZTF alert dictionary into a dataframe.

    Adapted from:
    https://github.com/ZwickyTransientFacility/ztf-avro-alert/blob/master/notebooks/Filtering_alerts.ipynb
    """
    dfc = pd.DataFrame(alert_dict["candidate"], index=[0])
    df_prv = pd.DataFrame(alert_dict["prv_candidates"])
    df = pd.concat([dfc, df_prv], ignore_index=True, sort=True)
    df = df[dfc.columns]  # return to original column ordering

    # we'll attach some metadata--note this may not be preserved after all operations
    # https://stackoverflow.com/questions/14688306/adding-meta-information-metadata-to-pandas-dataframe
    df.objectId = alert_dict["objectId"]
    return df


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


# --- Other
def class_defaults(cls):
    """Return dictionary of default values for args of cls.__init__."""
    params = inspect.signature(cls.__init__).parameters
    ClassDefaults = namedtuple(
        "ClassDefaults", " ".join(name for name in params.keys())
    )
    return ClassDefaults._make(params[key].default for key in ClassDefaults._fields)
    # return dict((name, param.default) for name, param in params.items())
