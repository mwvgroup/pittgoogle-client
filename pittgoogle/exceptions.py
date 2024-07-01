# -*- coding: UTF-8 -*-
class BadRequest(Exception):
    """Raised when a Flask request json envelope (e.g., from Cloud Run) is invalid."""


class CloudConnectionError(Exception):
    """Raised when a problem is encountered while trying to a Google Cloud resource."""


class OpenAlertError(Exception):
    """Raised when unable to deserialize a Pub/Sub message payload."""


class SchemaNotFoundError(Exception):
    """Raised when a schema with a given name is not found in the registry."""
