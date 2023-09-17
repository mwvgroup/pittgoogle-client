# -*- coding: UTF-8 -*-
class BadRequest(Exception):
    """Raised when a Flask request json envelope (e.g., from Cloud Run) is invalid."""


class OpenAlertError(Exception):
    """Raised when unable to deserialize a Pub/Sub message payload."""
