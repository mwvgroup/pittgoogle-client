# -*- coding: UTF-8 -*-
"""Tools for interacting with Pitt-Google Broker data resources on Google Cloud Platform."""
import logging
import os

try:
    from importlib import metadata

except ImportError:  # for Python<3.8
    import importlib_metadata as metadata

from .auth import Auth
from .alert import Alert
from .bigquery import Table
from .pubsub import Topic, Subscription, Consumer
from .registry import ProjectIds, Schemas
from . import exceptions, types_, registry, utils, auth, alert, bigquery, pubsub


__version__ = metadata.version("pittgoogle-client")

for var in ["GOOGLE_CLOUD_PROJECT", "GOOGLE_APPLICATION_CREDENTIALS"]:
    if var not in os.environ:
        logger = logging.getLogger(__name__)
        logger.warning(
            f"Warning: The environment variable {var} is not set. "
            "This may impact your ability to connect to your Google Cloud Platform project."
        )
