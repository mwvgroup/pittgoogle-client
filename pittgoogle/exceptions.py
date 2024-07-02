# -*- coding: UTF-8 -*-
class BadRequest(Exception):
    """Raised when a Flask request json envelope (e.g., from Cloud Run) is invalid."""


class CloudConnectionError(Exception):
    """Raised when a problem is encountered while trying to a Google Cloud resource."""


class SchemaError(Exception):
    """Raised when a schema with a given name is not found in the registry."""
