#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

"""Tools for interacting with Pitt-Google Broker data resources."""

import importlib.metadata
import logging
import os as os

from . import bigquery, figures, pubsub, utils

__version__ = importlib.metadata.version(__package__)

logger = logging.getLogger(__name__)

env_vars = ["GOOGLE_CLOUD_PROJECT", "GOOGLE_APPLICATION_CREDENTIALS"]
for var in env_vars:
    if var not in os.environ:
        logger.warning(
            f"Warning: The environment variable {var} is not set. "
            "This may impact your ability to connect to your "
            "Google Cloud Platform project."
        )
