import random
from pathlib import Path

import attrs

import pittgoogle


@attrs.define(kw_only=True)
class TestAlert:
    """Container for a single sample alert."""

    path: Path | None = attrs.field(default=None)
    dict_: dict | None = attrs.field(default=None)
    schema_name: str | None = attrs.field(default=None)
    schema_version: str | None = attrs.field(default=None)
    survey: str | None = attrs.field(default=None)

    @property
    def pgalert(self) -> pittgoogle.Alert:
        return pittgoogle.Alert.from_dict(self.dict_, schema_name=self.schema_name)
