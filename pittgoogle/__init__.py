#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

"""Tools for interacting with Pitt-Google Broker data resources."""

from . import bigquery, figures, pubsub, utils
import pkg_resources  # part of setuptools
import os as _os

# from warnings import warn as _warn
import logging


logger = logging.getLogger(__name__)


__version__ = pkg_resources.require("pittgoogle-client")[0].version


env_vars = ["GOOGLE_CLOUD_PROJECT", "GOOGLE_APPLICATION_CREDENTIALS"]
for var in env_vars:
    if var not in _os.environ:
        logger.warning(
            f"Warning: The environment variable {var} is not set. "
            "This may impact your ability to connect to your "
            "Google Cloud Platform project."
        )
