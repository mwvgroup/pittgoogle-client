# -*- coding: UTF-8 -*-
"""Exceptions.

.. autosummary::

    BadRequest
    CloudConnectionError
    SchemaError

----
"""


class BadRequest(Exception):
    """Raised when a Flask request json envelope (e.g., from Cloud Run) is invalid."""


class CloudConnectionError(Exception):
    """Raised when a problem is encountered while trying to connect to a Google Cloud resource."""


class SchemaError(Exception):
    """Raised when the schema cannot be found in the registry or is incompatible with the data."""
