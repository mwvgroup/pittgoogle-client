#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""Pitt-Google types."""

from typing import NamedTuple


class PittGoogleProjectIds(NamedTuple):
    """Pitt-Google broker's Google Cloud project IDs."""

    production: str = "ardent-cycling-243415"
    testing: str = "avid-heading-329016"
    billing: str = "light-cycle-328823"
