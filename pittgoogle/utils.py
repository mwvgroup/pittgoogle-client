# -*- coding: UTF-8 -*-
"""Classes and functions to support working with alerts and related data.

.. autosummary::

    Cast

----
"""
import base64
import io
import json
import logging
from typing import TYPE_CHECKING

import attrs
import fastavro

if TYPE_CHECKING:
    import astropy.table

LOGGER = logging.getLogger(__name__)


@attrs.define
class Cast:
    """Methods to convert data types."""

    @staticmethod
    def bytes_to_b64utf8(bytes_data):
        """Convert bytes data to UTF-8.

        Args:
            bytes_data (bytes):
                Data to be converted to UTF-8.

        Returns:
            str:
                The ``bytes_data`` converted to a string in UTF-8 format.
        """
        if bytes_data is not None:
            return base64.b64encode(bytes_data).decode("utf-8")

    @staticmethod
    def json_to_dict(bytes_data):
        """Converts JSON serialized bytes data to a dictionary.

        Args:
            bytes_data (bytes):
                Data to be converted to a dictionary.

        Returns:
            dict:
                The unpacked dictionary from the ``bytes_data``.
        """
        if bytes_data is not None:
            return json.loads(bytes_data)

    @staticmethod
    def b64json_to_dict(bytes_data):
        """Converts base64 encoded, JSON serialized bytes data to a dictionary.

        Args:
            bytes_data (Base64):
                Data to be converted to a dictionary.

        Returns:
            dict:
                The unpacked dictionary from the ``bytes_data``.
        """
        if bytes_data is not None:
            return Cast.json_to_dict(base64.b64decode(bytes_data))

    @staticmethod
    def avro_to_dict(bytes_data):
        """Converts Avro serialized bytes data to a dictionary.

        Args:
            bytes_data (bytes):
                Avro serialized bytes data to be converted to a dictionary. The schema must be attached in the header.

        Returns:
            dict:
                The unpacked dictionary from the ``bytes_data``.
        """
        if bytes_data is not None:
            with io.BytesIO(bytes_data) as fin:
                alert_dicts = list(fastavro.reader(fin))  # list with single dict
            if len(alert_dicts) != 1:
                LOGGER.warning(f"Expected 1 Avro record. Found {len(alert_dicts)}.")
            return alert_dicts[0]

    @staticmethod
    def b64avro_to_dict(bytes_data):
        """Converts base64 encoded, Avro serialized bytes data to a dictionary.

        Args:
            bytes_data (bytes):
                Base64 encoded, Avro serialized bytes data to be converted to a dictionary.

        Returns:
            dict:
                The unpacked dictionary from the ``bytes_data``.
        """
        return Cast.avro_to_dict(base64.b64decode(bytes_data))

    # --- Work with alert dictionaries
    @staticmethod
    def alert_dict_to_table(alert_dict: dict) -> "astropy.table.Table":
        """Package a ZTF alert dictionary into an Astropy Table.

        Args:
            alert_dict (dict):
                A dictionary containing ZTF alert information.

        Returns:
            astropy.table.Table:
                An Astropy Table containing the alert information.

        """
        import astropy.table
        import collections

        # collect rows for the table
        candidate = collections.OrderedDict(alert_dict["candidate"])
        rows = [candidate]
        for prv_cand in alert_dict["prv_candidates"]:
            # astropy 3.2.1 cannot handle dicts with different keys (fixed by 4.1)
            prv_cand_tmp = {key: prv_cand.get(key, None) for key in candidate.keys()}
            rows.append(prv_cand_tmp)

        # create and return the table
        table = astropy.table.Table(rows=rows)
        table.meta["comments"] = f"ZTF objectId: {alert_dict['objectId']}"
        return table

    # dates
    @staticmethod
    def jd_to_readable_date(jd) -> str:
        """Converts a Julian date to a human-readable string.

        Args:
            jd (float):
                Datetime value in Julian format.

        Returns:
            str:
                The ``jd`` in the format 'day mon year hour:min'.
        """
        import astropy.time

        return astropy.time.Time(jd, format="jd").strftime("%d %b %Y - %H:%M:%S")


# --- Survey-specific
def ztf_fid_names() -> dict:
    """Return a dictionary mapping the ZTF `fid` (filter ID) to the common name."""

    return {1: "g", 2: "r", 3: "i"}
