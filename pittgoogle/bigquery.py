# -*- coding: UTF-8 -*-
"""Classes to facilitate connections to BigQuery datasets and tables."""
import logging

import attrs
import google.cloud.bigquery

from .alert import Alert
from .auth import Auth

LOGGER = logging.getLogger(__name__)


@attrs.define
class Table:
    """Methods and properties for a BigQuery table.

    Args:
        name (str):
            Name of the BigQuery table.
        dataset (str):
            Name of the BigQuery dataset this table belongs to.
        projectid (str, optional):
            The table owner's Google Cloud project ID. Either this or `auth` is required. Note:
            :attr:`pittgoogle.utils.ProjectIds` is a registry containing Pitt-Google's project IDs.
        auth (Auth, optional):
            Credentials for the Google Cloud project that owns this table.
            If not provided, it will be created from environment variables when needed.
        client (google.cloud.bigquery.Client, optional):
            BigQuery client that will be used to access the table.
            If not provided, a new client will be created the first time it is requested.

    ----
    """

    # Strings _below_ the field will make these also show up as individual properties in rendered docs.
    name: str = attrs.field()
    """Name of the BigQuery table."""
    dataset: str = attrs.field()
    """Name of the BigQuery dataset this table belongs to."""
    # The rest don't need string descriptions because they are explicitly defined as properties below.
    _projectid: str = attrs.field(default=None)
    _auth: Auth = attrs.field(
        default=None, validator=attrs.validators.optional(attrs.validators.instance_of(Auth))
    )
    _client: google.cloud.bigquery.Client | None = attrs.field(
        default=None,
        validator=attrs.validators.optional(
            attrs.validators.instance_of(google.cloud.bigquery.Client)
        ),
    )
    _table: google.cloud.bigquery.Table | None = attrs.field(default=None, init=False)

    @classmethod
    def from_cloud(
        cls,
        name: str,
        *,
        dataset: str | None = None,
        survey: str | None = None,
        testid: str | None = None,
    ):
        """Create a `Table` object using a `client` with implicit credentials.

        Use this method when creating a `Table` object in code running in Google Cloud (e.g.,
        in a Cloud Run module). The underlying Google APIs will automatically find your credentials.

        The table resource in Google BigQuery is expected to already exist.

        Args:
            name (str):
                Name of the table.
            dataset (str, optional):
                Name of the dataset containing the table. Either this or a `survey` is required.
                If a `testid` is provided, it will be appended to this name following the Pitt-Google
                naming syntax.
            survey (str, optional):
                Name of the survey. This will be used as the name of the dataset if the `dataset`
                kwarg is not provided. This kwarg is provided for convenience in cases where the
                Pitt-Google naming syntax is used to name resources.
            testid (str, optional):
                Pipeline identifier. If this is not `None`, `False`, or `"False"`, it will be
                appended to the dataset name. This is used in cases where the Pitt-Google naming
                syntax is used to name resources. This allows pipeline modules to find the correct
                resources without interfering with other pipelines that may have deployed resources
                with the same base names (e.g., for development and testing purposes).

        Returns:
            Table:
                The `Table` object.

        Raises:
            NotFound:
                # [TODO] Track down specific error raised when table doesn't exist; update this docstring.
        """
        if dataset is None:
            dataset = survey
        # if testid is not False, "False", or None, append it to the dataset
        if testid and testid != "False":
            dataset = f"{dataset}_{testid}"
        client = google.cloud.bigquery.Client()
        table = cls(name, dataset=dataset, projectid=client.project, client=client)
        # make the get request now to create a connection to the table
        _ = table.table
        return table

    @property
    def auth(self) -> Auth:
        """Credentials for the Google Cloud project that owns this table.

        This will be created using environment variables if necessary.
        """
        if self._auth is None:
            self._auth = Auth()

        if (self._projectid != self._auth.GOOGLE_CLOUD_PROJECT) and (self._projectid is not None):
            LOGGER.warning(f"setting projectid to match auth: {self._auth.GOOGLE_CLOUD_PROJECT}")
            self._projectid = self._auth.GOOGLE_CLOUD_PROJECT

        return self._auth

    @property
    def id(self) -> str:
        """Fully qualified table ID with syntax 'projectid.dataset_name.table_name'."""
        return f"{self.projectid}.{self.dataset}.{self.name}"

    @property
    def projectid(self) -> str:
        """The table owner's Google Cloud project ID."""
        if self._projectid is None:
            self._projectid = self.auth.GOOGLE_CLOUD_PROJECT
        return self._projectid

    @property
    def table(self) -> google.cloud.bigquery.Table:
        """Google Cloud BigQuery Table object that is connected to the Cloud resource.

        Makes a `get_table` request if necessary.

        Returns:
            google.cloud.bigquery.Table:
                The BigQuery Table object, connected to the Cloud resource.
        """
        if self._table is None:
            self._table = self.client.get_table(self.id)
        return self._table

    @property
    def client(self) -> google.cloud.bigquery.Client:
        """Google Cloud BigQuery Client used to access the table.

        This will be created using :attr:`Table.auth` if necessary.

        Returns:
            google.cloud.bigquery.Client:
                The BigQuery client instance.
        """
        if self._client is None:
            self._client = google.cloud.bigquery.Client(credentials=self.auth.credentials)
        return self._client

    def insert_rows(self, rows: list[dict | Alert]) -> list[dict]:
        """Inserts the rows into the BigQuery table.

        Args:
            rows (list[dict or Alert]):
                The rows to be inserted. Can be a list of dictionaries or a list of Alert objects.

        Returns:
            list[dict]:
                A list of errors encountered.
        """
        # if elements of rows are Alerts, need to extract the dicts
        myrows = [row.dict if isinstance(row, Alert) else row for row in rows]
        errors = self.client.insert_rows(self.table, myrows)
        if len(errors) > 0:
            LOGGER.warning(f"BigQuery insert error: {errors}")
        return errors
