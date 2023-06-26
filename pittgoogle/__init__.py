# -*- coding: UTF-8 -*-
"""Tools for interacting with Pitt-Google Broker data resources on Google Cloud Platform."""
import logging
import os as os
from pathlib import Path

from . import auth, bigquery, exceptions, figures, pubsub, utils


logger = logging.getLogger(__name__)


pkg_root = Path(__file__).parent.parent
with open(os.path.join(pkg_root, "VERSION.txt")) as version_file:
    __version__ = version_file.read().strip()


env_vars = ["GOOGLE_CLOUD_PROJECT", "GOOGLE_APPLICATION_CREDENTIALS"]
for var in env_vars:
    if var not in os.environ:
        logger.warning(
            f"Warning: The environment variable {var} is not set. "
            "This may impact your ability to connect to your Google Cloud Platform project."
        )
