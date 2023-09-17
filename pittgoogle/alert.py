# -*- coding: UTF-8 -*-
"""Classes to facilitate working with astronomical alerts.

.. contents::
   :local:
   :depth: 2

Usage Examples
---------------

Load an alert from disk:

.. code-block:: python

    import pittgoogle

    path = "path/to/ztf_alert.avro"  # point this to a file containing an alert
    alert = pittgoogle.Alert.from_path(path, schema_name="ztf")

Load a ZTF alert from a Pub/Sub message that has triggered a Cloud Run module:

.. code-block:: python

    import pittgoogle
    # flask is used to work with HTTP requests, which trigger Cloud Run modules
    # the request contains the Pub/Sub message, which contains the alert packet
    from flask import Flask, request

    app = Flask(__name__)

    # function that receives the request
    @app.route("/", methods=["POST"])
    def index():

        try:
            # unpack the alert
            # if the request does not contain a valid message, this raises a `BadRequest`
            alert = pittgoogle.Alert.from_cloud_run(envelope=request.get_json(), schema_name="ztf")

        except pg.exceptions.BadRequest as err:
            # return the error text and an HTTP 400 Bad Request code
            return err.text, 400

        # continue processing the alert
        # when finished, return an empty string and an HTTP success code
        return "", 204

API
----

"""
import importlib.resources
import io
import logging
from typing import TYPE_CHECKING, Optional, Union

import fastavro
import yaml
from attrs import define, field
from google.cloud import pubsub_v1

from .exceptions import BadRequest, OpenAlertError
from .utils import Cast

if TYPE_CHECKING:
    import google.protobuf.timestamp_pb2
    import google._upb._message
    import pandas as pd  # always lazy-load pandas. it hogs memory on cloud functions and run


LOGGER = logging.getLogger(__name__)
PACKAGE_DIR = importlib.resources.files(__package__)


@define(frozen=True)
class _PubsubMessageLike:
    """Container for an incoming Pub/Sub message that mimics a `pubsub_v1.types.PubsubMessage`.

    It is convenient for the `Alert` class to work with a message as a
    `pubsub_v1.types.PubsubMessage`. However, there are many ways to obtain an alert that do
    not result in a `pubsub_v1.types.PubsubMessage` (e.g., an alert packet loaded from disk or
    an incoming message to a Cloud Functions or Cloud Run module). In those cases, this class
    is used to create an object with the same attributes as a `pubsub_v1.types.PubsubMessage`.
    This object is then assigned to the `msg` attribute of the `Alert`.
    """

    data: bytes = field()
    attributes: dict = field(factory=dict)
    message_id: Optional[str] = field(default=None)
    publish_time: Optional["google.protobuf.timestamp_pb2.Timestamp"] = field(default=None)
    ordering_key: Optional[str] = field(default=None)


@define(kw_only=True)
class Alert:
    """Pitt-Google container for an astronomical alert.

    Alerts are typically loaded from a Pub/Sub message but may also be loaded from a file.
    It is recommended to instantiate an `Alert` using one of the `from_*` methods.

    All parameters are keyword only.

    Parameters
    ------------
    bytes : `bytes`, optional
        The message payload, as returned by Pub/Sub. It may be Avro or JSON serialized depending
        on the topic.
    dict : `dict`, optional
        The message payload as a dictionary.
    metadata : `dict`, optional
        The message metadata.
    msg : `google.cloud.pubsub_v1.types.PubsubMessage`, optional
        The Pub/Sub message object, documented at
        `<https://cloud.google.com/python/docs/reference/pubsub/latest/google.cloud.pubsub_v1.types.PubsubMessage>`__.
    schema_name : `str`
        One of (case insensitive):
            - ztf
            - ztf.lite
            - elasticc.v0_9_1.alert
            - elasticc.v0_9_1.brokerClassification
        Schema name of the alert. Used for unpacking. If not provided, some properties of the
        `Alert` may not be available.
    """

    msg: Optional[Union["pubsub_v1.types.PubsubMessage", _PubsubMessageLike]] = field(default=None)
    """Incoming Pub/Sub message object."""
    _attributes: Optional[Union[dict, "google._upb._message.ScalarMapContainer"]] = field(
        default=None
    )
    _dict: Optional[dict] = field(default=None)
    _dataframe: Optional["pd.DataFrame"] = field(default=None)
    schema_name: str = field(factory=str, converter=str.lower)
    _schema_map: Optional[dict] = field(default=None)

    # ---- class methods ---- #
    @classmethod
    def from_msg(cls, msg, schema_name=str()) -> "Alert":  # [TODO] update tom_desc to use this
        """Create an `Alert` from a `pubsub_v1.types.PubsubMessage`."""
        return cls(msg=msg, schema_name=schema_name)

    @classmethod
    def from_cloud_run(cls, envelope: dict, schema_name: str = str()) -> "Alert":
        # check whether received message is valid, as suggested by Cloud Run docs
        if not envelope:
            raise BadRequest("Bad Request: no Pub/Sub message received")
        if not isinstance(envelope, dict) or "message" not in envelope:
            raise BadRequest("Bad Request: invalid Pub/Sub message format")

        return cls(
            msg=_PubsubMessageLike(
                # this class requires data. the rest should be present in the message, but let's be lenient
                data=envelope["message"]["data"],
                attributes=envelope["message"].get("attributes"),
                message_id=envelope["message"].get("message_id"),
                publish_time=envelope["message"].get("publish_time"),
                ordering_key=envelope["message"].get("ordering_key"),
            ),
            schema_name=schema_name,
        )

    @classmethod
    def from_path(cls, path, schema_name=str()) -> "Alert":
        with open(path, "rb") as f:
            bytes = f.read()
        return cls(msg=_PubsubMessageLike(data=bytes), schema_name=schema_name)

    # ---- properties ---- #
    @property
    def attributes(self) -> Union[dict, "google._upb._message.ScalarMapContainer"]:
        """Custom metadata for the message. Pub/Sub handles this as a dict-like called "attributes".

        If None, this will be set to `self.msg.attributes`.
        Update as desired.
        When publishing, this will be sent as the message attributes.
        """
        if self._attributes is None:
            self._attributes = self.msg.attributes
        return self._attributes

    @property
    def dict(self) -> dict:
        """Message payload as a dictionary. Created from `self.msg.data` and `self.schema_name`, if needed.

        Raises
        ------
        :class:`pittgoogle.exceptions.OpenAlertError`
            if unable to deserialize the alert bytes.
        """
        if self._dict is not None:
            return self._dict

        if self.schema_name.startswith("elasticc"):
            # self.msg.data is avro and schemaless. load the schema, then convert the bytes to a dict
            schemapath = PACKAGE_DIR / f"schemas/elasticc/{self.schema_name}.avsc"
            schema = fastavro.schema.load_schema(schemapath)
            with io.BytesIO(self.msg.data) as fin:
                self._dict = fastavro.schemaless_reader(fin, schema)
            return self._dict

        if self.schema_name == "":
            LOGGER.warning("no alert schema_name provided. attempting to deserialize without it.")

        # assume this is a ztf or ztf-lite alert
        # this should be rewritten to catch specific errors
        # for now, just try avro then json, catching basically all errors in the process
        try:
            self._dict = Cast.avro_to_dict(self.msg.data)
        except Exception:
            try:
                self._dict = Cast.json_to_dict(self.msg.data)
            except Exception:
                raise OpenAlertError("failed to deserialize the alert bytes")
        return self._dict

    @property
    def dataframe(self) -> "pd.DataFrame":
        if self._dataframe is None:
            import pandas as pd  # lazy-load pandas. it hogs memory on cloud functions and run

            if self.schema_name.endswith(".lite"):
                src_df = pd.DataFrame(self.dict["source"], index=[0])
                prvs_df = pd.DataFrame(self.dict["prv_sources"])
            else:
                src_df = pd.DataFrame(self.dict[self.schema_map["source"]], index=[0])
                prvs_df = pd.DataFrame(self.dict[self.schema_map["prv_sources"]])
            self._dataframe = pd.concat([src_df, prvs_df], ignore_index=True)

        return self._dataframe

    @property
    def alertid(self) -> Union[str, int]:
        """Convenience property for the alert ID. If the survey does not define an alert ID, this is the `sourceid`."""
        return self.get("alertid", self.sourceid)

    @property
    def objectid(self) -> Union[str, int]:
        """Convenience property for the object ID. The "object" represents a collection of sources, as determined by the survey."""
        return self.get("objectid")

    @property
    def sourceid(self) -> Union[str, int]:
        """Convenience property for the source ID. The "source" is the detection that triggered the alert."""
        return self.get("sourceid")

    @property
    def schema_map(self) -> dict:
        if self._schema_map is None:
            if self.schema_name == str():
                raise TypeError("no alert schema_name provided. unable to load schema map.")
            survey = self.schema_name.split(".")[0]
            path = PACKAGE_DIR / f"schemas/maps/{survey}.yml"
            self._schema_map = yaml.safe_load(path.read_text())
        return self._schema_map

    # ---- methods ---- #
    def get(self, key: str, default: Optional[str] = None):
        # if key is found in self.dict, just return the corresponding value
        if key in self.dict:
            return self.dict.get(key)

        # lookup the key in the schema map
        survey_key = self.schema_map.get(key)  # str or list[str]

        if isinstance(survey_key, str):
            return self.dict.get(survey_key)

        if not isinstance(survey_key, list):
            return default

        if len(survey_key) == 1:
            return self.dict.get(survey_key[0])

        if len(survey_key) == 2:
            return self.dict.get(survey_key[0]).get(survey_key[1])

        if len(survey_key) == 3:
            return self.dict.get(survey_key[0]).get(survey_key[1]).get(survey_key[2])

    def get_key(self, key, name_only: bool = True):
        if key in self.dict:
            return key

        survey_key = self.schema_map.get(key)  # str or list[str]

        if isinstance(survey_key, str):
            return survey_key

        if not isinstance(survey_key, list):
            return

        if name_only:
            return survey_key[-1]

        return survey_key
