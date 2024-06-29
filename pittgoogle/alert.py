# -*- coding: UTF-8 -*-
"""Classes to facilitate working with astronomical alerts."""
import base64
import importlib.resources
import io
import logging
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, Mapping, Optional, Union

import fastavro
from attrs import define, field

from . import registry, types_, utils
from .exceptions import BadRequest, OpenAlertError, SchemaNotFoundError

if TYPE_CHECKING:
    import google.cloud.pubsub_v1
    import pandas as pd  # always lazy-load pandas. it hogs memory on cloud functions and run

LOGGER = logging.getLogger(__name__)
PACKAGE_DIR = importlib.resources.files(__package__)


@define(kw_only=True)
class Alert:
    """Pitt-Google container for an astronomical alert.

    Instances of this class are returned by other calls like :meth:`pittgoogle.Subscription.pull_batch`,
    so it is often not necessary to instantiate this directly.
    In cases where you do want to create an `Alert` directly, use one of the `from_*` methods like `pittgoogle.Alert.from_dict`.

    All parameters are keyword only.

    Parameters
    ----------
    bytes : `bytes` (optional)
        The message payload, as returned by Pub/Sub. It may be Avro or JSON serialized depending
        on the topic.
    dict : `dict` (optional)
        The message payload as a dictionary.
    metadata : `dict` (optional)
        The message metadata.
    msg : `google.cloud.pubsub_v1.types.PubsubMessage` (optional)
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

    msg: Optional[
        Union["google.cloud.pubsub_v1.types.PubsubMessage", types_.PubsubMessageLike]
    ] = field(default=None)
    """Incoming Pub/Sub message object."""
    _attributes: Optional[Mapping[str, str]] = field(default=None)
    _dict: Optional[Dict] = field(default=None)
    _dataframe: Optional["pd.DataFrame"] = field(default=None)
    schema_name: Optional[str] = field(default=None)
    _schema: Optional[types_.Schema] = field(default=None, init=False)
    path: Optional[Path] = field(default=None)

    # ---- class methods ---- #
    @classmethod
    def from_cloud_run(cls, envelope: Dict, schema_name: Optional[str] = None) -> "Alert":
        """Create an `Alert` from an HTTP request envelope containing a Pub/Sub message, as received by a Cloud Run module.

        Parameters
        ----------
        envelope : dict
            The HTTP request envelope containing the Pub/Sub message.
        schema_name : str (optional)
            The name of the schema to use. Defaults to None.

        Returns
        -------
            Alert : An instance of the `Alert` class.

        Raises
        ------
            BadRequest : If the Pub/Sub message is invalid or missing.

        Example
        -------
        Code for a Cloud Run module that uses this method to open a ZTF alert:

        .. code-block:: python

            import pittgoogle
            # flask is used to work with HTTP requests, which trigger Cloud Run modules
            # the request contains the Pub/Sub message, which contains the alert packet
            import flask

            app = flask.Flask(__name__)

            # function that receives the request
            @app.route("/", methods=["POST"])
            def index():

                try:
                    # unpack the alert
                    # if the request does not contain a valid message, this raises a `BadRequest`
                    alert = pittgoogle.Alert.from_cloud_run(envelope=flask.request.get_json(), schema_name="ztf")

                except pittgoogle.exceptions.BadRequest as exc:
                    # return the error text and an HTTP 400 Bad Request code
                    return str(exc), 400

                # continue processing the alert
                # when finished, return an empty string and an HTTP success code
                return "", 204
        """
        # check whether received message is valid, as suggested by Cloud Run docs
        if not envelope:
            raise BadRequest("Bad Request: no Pub/Sub message received")
        if not isinstance(envelope, dict) or "message" not in envelope:
            raise BadRequest("Bad Request: invalid Pub/Sub message format")

        # convert the message publish_time string -> datetime
        # occasionally the string doesn't include microseconds so we need a try/except
        publish_time = envelope["message"]["publish_time"].replace("Z", "+00:00")
        try:
            publish_time = datetime.strptime(publish_time, "%Y-%m-%dT%H:%M:%S.%f%z")
        except ValueError:
            publish_time = datetime.strptime(publish_time, "%Y-%m-%dT%H:%M:%S%z")

        return cls(
            msg=types_.PubsubMessageLike(
                # data is required. the rest should be present in the message, but use get to be lenient
                data=base64.b64decode(envelope["message"]["data"].encode("utf-8")),
                attributes=envelope["message"].get("attributes"),
                message_id=envelope["message"].get("message_id"),
                publish_time=publish_time,
                ordering_key=envelope["message"].get("ordering_key"),
            ),
            schema_name=schema_name,
        )

    @classmethod
    def from_dict(
        cls,
        payload: Dict,
        attributes: Optional[Mapping[str, str]] = None,
        schema_name: Optional[str] = None,
    ) -> "Alert":
        """Create an `Alert` object from the given `payload` dictionary.

        Parameters
        ----------
        payload : dict
            The dictionary containing the data for the `Alert` object.
        attributes : dict-like (optional)
            Additional attributes for the `Alert` object. Defaults to None.
        schema_name : str (optional)
            The name of the schema. Defaults to None.

        Returns
        -------
            Alert: An instance of the `Alert` class.
        """
        return cls(dict=payload, attributes=attributes, schema_name=schema_name)

    @classmethod
    def from_msg(cls, msg, schema_name: Optional[str] = None) -> "Alert":
        # [FIXME] This type hint is causing an error when building docs.
        #   Warning, treated as error:
        #   Cannot resolve forward reference in type annotations of "pittgoogle.alert.Alert.from_msg":
        #   name 'google' is not defined
        # cls, msg: "google.cloud.pubsub_v1.types.PubsubMessage", schema_name: Optional[str] = None
        """
        Create an `Alert` object from a `google.cloud.pubsub_v1.types.PubsubMessage`.

        Parameters
        ----------
        msg : `google.cloud.pubsub_v1.types.PubsubMessage`
            The PubsubMessage object to create the Alert from.
        schema_name : str (optional)
            The name of the schema to use for the Alert. Defaults to None.

        Returns
        -------
        Alert : The created `Alert` object.
        """
        return cls(msg=msg, schema_name=schema_name)

    @classmethod
    def from_path(cls, path: Union[str, Path], schema_name: Optional[str] = None) -> "Alert":
        """Create an `Alert` object from the file at `path`.

        Parameters
        ----------
        path : str or Path
            The path to the file containing the alert data.
        schema_name : str, optional
            The name of the schema to use for the alert, by default None.

        Returns
        -------
        Alert
            An instance of the `Alert` class.
        """
        with open(path, "rb") as f:
            bytes_ = f.read()
        return cls(
            msg=types_.PubsubMessageLike(data=bytes_), schema_name=schema_name, path=Path(path)
        )

    # ---- properties ---- #
    @property
    def attributes(self) -> Dict:
        """Custom metadata for the message. Pub/Sub handles this as a dict-like called "attributes".

        If this was not set when the `Alert` was instantiated, a new dictionary will be created using
        the `attributes` field in :attr:`pittgoogle.Alert.msg` the first time it is requested.
        Update this dictionary as desired.
        Updates will not affect the original `msg`.
        When publishing the alert using :attr:`pittgoogle.Topic.publish`, this dictionary will be
        sent as the Pub/Sub message attributes.
        """
        if self._attributes is None:
            self._attributes = dict(self.msg.attributes)
        return self._attributes

    @property
    def dict(self) -> Dict:
        """Alert data as a dictionary. Created from `self.msg.data`, if needed.

        Raises
        ------
        :class:`pittgoogle.exceptions.OpenAlertError`
            If unable to deserialize the alert bytes.
        """
        if self._dict is not None:
            return self._dict

        # deserialize self.msg.data (avro or json bytestring) into a dict.
        # if self.msg.data is either (1) json; or (2) avro that contains the schema in the header,
        # self.schema is not required for deserialization, so we want to be lenient.
        # if self.msg.data is schemaless avro, deserialization requires self.schema.avsc to exist.
        # currently, there is a clean separation between surveys:
        #     elasticc always requires self.schema.avsc; ztf never does.
        # we'll check the survey name from self.schema.survey; but first we need to check whether
        # the schema exists so we can try to continue without one instead of raising an error.
        # we may want or need to handle this differently in the future.
        try:
            self.schema
        except SchemaNotFoundError as exc:
            LOGGER.warning(f"schema not found. attempting to deserialize without it. {exc}")
            avro_schema = None
        else:
            if self.schema.survey in ["elasticc"]:
                avro_schema = self.schema.avsc
            else:
                avro_schema = None

        # if we have an avro schema, use it to deserialize and return
        if avro_schema:
            with io.BytesIO(self.msg.data) as fin:
                self._dict = fastavro.schemaless_reader(fin, avro_schema)
            return self._dict

        # [TODO] this should be rewritten to catch specific errors
        # for now, just try avro then json, catching basically all errors in the process
        try:
            self._dict = utils.Cast.avro_to_dict(self.msg.data)
        except Exception:
            try:
                self._dict = utils.Cast.json_to_dict(self.msg.data)
            except Exception:
                raise OpenAlertError("failed to deserialize the alert bytes")
        return self._dict

    @property
    def dataframe(self) -> "pd.DataFrame":
        """Return a pandas DataFrame containing the source detections."""
        if self._dataframe is not None:
            return self._dataframe

        import pandas as pd  # always lazy-load pandas. it hogs memory on cloud functions and run

        # sources and previous sources are expected to have the same fields
        sources_df = pd.DataFrame([self.get("source")] + self.get("prv_sources"))
        # sources and forced sources may have different fields
        forced_df = pd.DataFrame(self.get("prv_forced_sources"))

        # use nullable integer data type to avoid converting ints to floats
        # for columns in one dataframe but not the other
        sources_ints = [c for c, v in sources_df.dtypes.items() if v == int]
        sources_df = sources_df.astype(
            {c: "Int64" for c in set(sources_ints) - set(forced_df.columns)}
        )
        forced_ints = [c for c, v in forced_df.dtypes.items() if v == int]
        forced_df = forced_df.astype(
            {c: "Int64" for c in set(forced_ints) - set(sources_df.columns)}
        )

        self._dataframe = pd.concat([sources_df, forced_df], ignore_index=True)
        return self._dataframe

    @property
    def alertid(self) -> Union[str, int]:
        """Convenience property to get the alert ID.

        If the survey does not define an alert ID, this returns the `sourceid`.
        """
        return self.get("alertid", self.sourceid)

    @property
    def objectid(self) -> Union[str, int]:
        """Convenience property to get the object ID.

        The "object" represents a collection of sources, as determined by the survey.
        """
        return self.get("objectid")

    @property
    def sourceid(self) -> Union[str, int]:
        """Convenience property to get the source ID.

        The "source" is the detection that triggered the alert.
        """
        return self.get("sourceid")

    @property
    def schema(self) -> types_.Schema:
        """Loads the schema from the registry :class:`pittgoogle.registry.Schemas`.

        Raises
        ------
        :class:`pittgoogle.exceptions.SchemaNotFoundError`
            if the `schema_name` is not supplied or a schema with this name is not found
        """
        if self._schema is not None:
            return self._schema

        # need to load the schema. raise an error if no schema_name given
        if self.schema_name is None:
            raise SchemaNotFoundError("a schema_name is required")

        # this also may raise SchemaNotFoundError
        self._schema = registry.Schemas.get(self.schema_name)
        return self._schema

    # ---- methods ---- #
    def add_id_attributes(self) -> None:
        """Add the IDs to the attributes. ("alertid", "objectid", "sourceid")"""
        ids = ["alertid", "objectid", "sourceid"]
        values = [self.get(id) for id in ids]

        # get the survey-specific field names
        survey_names = [self.get_key(id) for id in ids]
        # if the field is nested, the key will be a list
        # but pubsub message attributes must be strings. join to avoid a future error on publish
        names = [".".join(id) if isinstance(id, list) else id for id in survey_names]

        # only add to attributes if the survey has defined this field
        for idname, idvalue in zip(names, values):
            if idname is not None:
                self.attributes[idname] = idvalue

    def get(self, field: str, default: Any = None) -> Any:
        """Return the value of `field` in this alert.

        The keys in the alert dictionary :attr:`pittgoogle.alert.Alert.dict` are survey-specific field names.
        This method allows you to `get` values from the dict using generic names that will work across
        surveys. `self.schema.map` is the mapping of generic -> survey-specific names.
        To access a field using a survey-specific name, get it directly from the alert `dict`.

        Parameters
        ----------
        field : str
            Name of a field in the alert's schema. This must be one of the keys in the dict `self.schema.map`.
        default : str or None
            Default value to be returned if the field is not found.

        Returns
        -------
        value : any
            Value in the :attr:`pittgoogle.alert.Alert.dict` corresponding to this field.
        """
        survey_field = self.schema.map.get(field)  # str, list[str], or None

        if survey_field is None:
            return default

        if isinstance(survey_field, str):
            return self.dict.get(survey_field, default)

        # if survey_field is not one of the expected types, the schema map is malformed
        # maybe this was intentional, but we don't know how to handle it here
        if not isinstance(survey_field, list):
            raise TypeError(
                f"field lookup not implemented for a schema-map value of type {type(survey_field)}"
            )

        # the list must have more than 1 item, else it would be a single str
        if len(survey_field) == 2:
            try:
                return self.dict[survey_field[0]][survey_field[1]]
            except KeyError:
                return default

        if len(survey_field) == 3:
            try:
                return self.dict[survey_field[0]][survey_field[1]][survey_field[2]]
            except KeyError:
                return default

        raise NotImplementedError(
            f"field lookup not implemented for depth {len(survey_field)} (key = {survey_field})"
        )

    def get_key(
        self, field: str, name_only: bool = False, default: Optional[str] = None
    ) -> Optional[Union[str, list[str]]]:
        """Return the survey-specific field name.

        Parameters
        ----------
        field : str
            Generic field name whose survey-specific name is to be returned. This must be one of the
            keys in the dict `self.schema.map`.
        name_only : bool
            In case the survey-specific field name is nested below the top level, whether to return
            just the single final name as a str (True) or the full path as a list[str] (False).
        default : str or None
            Default value to be returned if the field is not found.

        Returns
        -------
        survey_field : str or list[str]
            Survey-specific name for the `field`, or `default` if the field is not found.
            list[str] if this is a nested field and `name_only` is False, else str with the
            final field name only.
        """
        survey_field = self.schema.map.get(field)  # str, list[str], or None

        if survey_field is None:
            return default

        if name_only and isinstance(survey_field, list):
            return survey_field[-1]

        return survey_field
