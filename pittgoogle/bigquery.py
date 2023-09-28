# -*- coding: UTF-8 -*-
"""Classes to facilitate connections to BigQuery datasets and tables.

.. contents::
   :local:
   :depth: 2

.. note::

    This module relies on :mod:`pittgoogle.auth` to authenticate API calls.
    The examples given below assume the use of a :ref:`service account <service account>` and
    :ref:`environment variables <set env vars>`. In this case, :mod:`pittgoogle.auth` does not
    need to be called explicitly.

Usage Examples
---------------

.. code-block:: python

    import pittgoogle

    [TODO]

API
----

"""
import logging
from typing import TYPE_CHECKING, Optional, Union

import google.cloud.bigquery as bigquery
from attrs import define, field
from attrs.validators import instance_of, optional

from .auth import Auth

if TYPE_CHECKING:
    from . import Alert


LOGGER = logging.getLogger(__name__)


@define
class Table:
    """Methods and properties for a BigQuery table.

    Parameters
    ------------
    name : `str`
        Name of the BigQuery table.
    dataset : `str`
        Name of the BigQuery dataset this table belongs to.

    projectid : `str`, optional
        The topic owner's Google Cloud project ID. Either this or `auth` is required. Use this
        if you are connecting to a subscription owned by a different project than this topic. Note:
        :attr:`pittgoogle.utils.ProjectIds` is a registry containing Pitt-Google's project IDs.
    auth : :class:`pittgoogle.auth.Auth`, optional
        Credentials for the Google Cloud project that owns this topic. If not provided,
        it will be created from environment variables when needed.
    client : `pubsub_v1.PublisherClient`, optional
        Pub/Sub client that will be used to access the topic. If not provided, a new client will
        be created (using `auth`) the first time it is requested.
    """

    name: str = field()
    dataset: str = field()
    projectid: str = field(default=None)
    _auth: Auth = field(default=None, validator=optional(instance_of(Auth)))
    _client: Optional[bigquery.Client] = field(
        default=None, validator=optional(instance_of(bigquery.Client))
    )
    _table: Optional[bigquery.Table] = field(default=None, init=False)

    @classmethod
    def from_cloud(
        cls,
        name: str,
        *,
        dataset: Optional[str] = None,
        survey: Optional[str] = None,
        testid: Optional[str] = None,
    ):
        """Create a `Table` with a `client` using implicit credentials (no explicit `auth`).

        The `projectid` will be retrieved from the `client`.

        Parameters
        ----------
        name : `str`
            Name of the table.
        dataset : `str`, optional
            Name of the dataset containing the table. Either this or a `survey` is required. If a
            `testid` is provided, it will be appended to this name following the Pitt-Google naming syntax.
        survey : `str`, optional
            Name of the survey. This will be used as the name of the dataset if the `dataset` kwarg
            is not provided. This kwarg is provided for convenience in cases where the Pitt-Google
            naming syntax is used to name resources.
        testid : `str`, optional
            Pipeline identifier. If this is not `None`, `False`, or `"False"` it will be appended to
            the dataset name. This is used in cases where the Pitt-Google naming syntax is used to name
            resources. This allows pipeline modules to find the correct resources without interfering
            with other pipelines that may have deployed resources with the same base names
            (e.g., for development and testing purposes).
        """
        if dataset is None:
            # [TODO] update the elasticc broker to name the dataset using the survey name only
            dataset = survey
        # if testid is not False, "False", or None, append it to the dataset
        if testid and testid != "False":
            dataset = f"{dataset}_{testid}"
        client = bigquery.Client()
        table = cls(name, dataset=dataset, projectid=client.project, client=client)
        # make the get request now to create a connection to the table
        _ = table.table
        return table

    @property
    def auth(self) -> Auth:
        """Credentials for the Google Cloud project that owns this topic.

        This will be created from environment variables if `self._auth` is None.
        """
        if self._auth is None:
            self._auth = Auth()

        if (self.projectid != self._auth.GOOGLE_CLOUD_PROJECT) and (self.projectid is not None):
            LOGGER.warning(f"setting projectid to match auth: {self._auth.GOOGLE_CLOUD_PROJECT}")
        self.projectid = self._auth.GOOGLE_CLOUD_PROJECT

        return self._auth

    @property
    def id(self) -> str:
        """Fully qualified table ID."""
        # make sure we have a projectid. if it needs to be set, call auth
        if self.projectid is None:
            self.auth
        return f"{self.projectid}.{self.dataset}.{self.name}"

    @property
    def table(self) -> bigquery.Table:
        """Return a BigQuery Table object that's connected to the table. Makes a get request if necessary."""
        if self._table is None:
            self._table = self.client.get_table(self.id)
        return self._table

    @property
    def client(self) -> bigquery.Client:
        """BigQuery client for table access.

        Will be created using `self.auth.credentials` if necessary.
        """
        if self._client is None:
            self._client = bigquery.Client(credentials=self.auth.credentials)
        return self._client

    def insert_rows(self, alerts: Union["Alert", list["Alert"]]) -> list[dict]:
        rows = [alert.dict for alert in list(alerts)]
        errors = self.client.insert_rows(self.table, rows)
        if len(errors) > 0:
            LOGGER.warning(f"BigQuery insert error: {errors}")
        return errors
