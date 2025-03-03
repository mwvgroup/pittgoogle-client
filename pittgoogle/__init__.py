# -*- coding: UTF-8 -*-
"""Tools for interacting with Pitt-Google Broker data resources on Google Cloud Platform."""
import importlib.metadata
import importlib.resources
import logging
import os

# Do these first so the modules can import them.
__package_path__ = importlib.resources.files(__package__)
__version__ = importlib.metadata.version("pittgoogle-client")

from . import alert, auth, bigquery, exceptions, pubsub, registry, schema, types_, utils
from .alert import Alert
from .auth import Auth
from .bigquery import Table
from .pubsub import Consumer, Subscription, Topic
from .registry import ProjectIds, Schemas

for var in ["GOOGLE_CLOUD_PROJECT", "GOOGLE_APPLICATION_CREDENTIALS"]:
    if var not in os.environ:
        logger = logging.getLogger(__name__)
        logger.warning(
            f"Warning: The environment variable {var} is not set. "
            "This may impact your ability to connect to your Google Cloud Platform project."
        )
