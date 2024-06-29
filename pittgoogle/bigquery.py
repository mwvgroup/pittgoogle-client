# -*- coding: UTF-8 -*-
"""Classes to facilitate connections to BigQuery datasets and tables.

.. note::

    This module relies on :mod:`pittgoogle.auth` to authenticate API calls.
    The examples given below assume the use of a :ref:`service account <service account>` and
    :ref:`environment variables <set env vars>`.
"""
import logging
from typing import Optional, Union

import google.cloud.bigquery as bigquery
from attrs import define, field
from attrs.validators import instance_of, optional

from .alert import Alert
from .auth import Auth

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
        The table owner's Google Cloud project ID. Either this or `auth` is required. Note:
        :attr:`pittgoogle.utils.ProjectIds` is a registry containing Pitt-Google's project IDs.
    auth : :class:`pittgoogle.auth.Auth`, optional
        Credentials for the Google Cloud project that owns this table. If not provided,
        it will be created from environment variables when needed.
    client : `bigquery.Client`, optional
        BigQuery client that will be used to access the table. If not provided, a new client will
        be created (using `auth`) the first time it is requested.
    """

    name: str = field()
    dataset: str = field()
    _projectid: str = field(default=None)
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
        """Create a `Table` object using a `client` with implicit credentials.

        Useful when creating a `Table` object from within a Cloud Run module or similar.
        The table in Google BigQuery is expected to exist already.
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
        """Credentials for the Google Cloud project that owns this table.

        This will be created from environment variables if `self._auth` is None.
        """
        if self._auth is None:
            self._auth = Auth()

        if (self._projectid != self._auth.GOOGLE_CLOUD_PROJECT) and (self._projectid is not None):
            LOGGER.warning(f"setting projectid to match auth: {self._auth.GOOGLE_CLOUD_PROJECT}")
            self._projectid = self._auth.GOOGLE_CLOUD_PROJECT

        return self._auth

    @property
    def id(self) -> str:
        """Fully qualified table ID with syntax "projectid.dataset_name.table_name"."""
        return f"{self.projectid}.{self.dataset}.{self.name}"

    @property
    def projectid(self) -> str:
        """The table owner's Google Cloud project ID."""
        if self._projectid is None:
            self._projectid = self.auth.GOOGLE_CLOUD_PROJECT
        return self._projectid

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

    def insert_rows(self, rows: Union[list[dict], list[Alert]]) -> list[dict]:
        """Inserts rows into the BigQuery table.

        Parameters
        ----------
        rows : list[dict] or list[Alert]
            The rows to be inserted. Can be a list of dictionaries or a list of Alert objects.

        Returns
        -------
        list[dict]
            A list of errors encountered.
        """
        # if elements of rows are Alerts, need to extract the dicts
        myrows = [row.dict if isinstance(row, Alert) else row for row in rows]
        errors = self.client.insert_rows(self.table, myrows)
        if len(errors) > 0:
            LOGGER.warning(f"BigQuery insert error: {errors}")
        return errors
