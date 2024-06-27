# -*- coding: UTF-8 -*-
class BadRequest(Exception):
    """Raised when a Flask request json envelope (e.g., from Cloud Run) is invalid."""


class OpenAlertError(Exception):
    """Raised when unable to deserialize a Pub/Sub message payload."""


class PubSubInvalid(Exception):
    """Raised when an invalid Pub/Sub configuration is encountered."""

class SchemaNotFoundError(Exception):
    """Raised when a schema with a given name is not found in the registry."""
