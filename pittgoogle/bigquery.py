# -*- coding: UTF-8 -*-
"""Classes to facilitate connections to BigQuery datasets and tables."""
import logging
from typing import TYPE_CHECKING, Optional

import attrs
import google.cloud.bigquery

from .alert import Alert
from .auth import Auth

if TYPE_CHECKING:
    import pandas as pd  # always lazy-load pandas. it hogs memory on cloud functions and run

LOGGER = logging.getLogger(__name__)


@attrs.define
class Client:
    """A client for interacting with Google BigQuery.

    It handles authentication and provides methods for executing queries and managing datasets and tables.

    All attributes of the underlying Google API class ``google.cloud.bigquery.Client`` that are not
    explicitly implemented here are accessible using ``pittgoogle.bigquery.Client().<attribute>``,
    which is a shortcut for ``pittgoogle.bigquery.Client().client.<attribute>``.

    Args:
        auth (Auth):
            The authentication credentials for the Google Cloud project.

    Example:

        The google.cloud

    ----
    """

    _auth: Auth = attrs.field(
        default=None, validator=attrs.validators.optional(attrs.validators.instance_of(Auth))
    )
    _client: google.cloud.bigquery.Client | None = attrs.field(default=None, init=False)

    def __getattr__(self, attr):
        """If ``attr`` doesn't exist in this class, try getting it from the underlying ``google.cloud.bigquery.Client``.

        Raises:
            AttributeError:
                if ``attr`` doesn't exist in either the pittgoogle or google.cloud API.
        """
        try:
            return getattr(self.client, attr)
        except AttributeError as excep:
            msg = f"Neither 'pittgoogle.bigquery.Client' nor 'google.cloud.bigquery.Client' has attribute '{attr}'"
            raise AttributeError(msg) from excep

    @property
    def auth(self) -> Auth:
        """Credentials for the Google Cloud project that this client will be connected to.

        This will be created using environment variables if necessary.
        """
        if self._auth is None:
            self._auth = Auth()
        return self._auth

    @property
    def client(self) -> google.cloud.bigquery.Client:
        if self._client is None:
            self._client = google.cloud.bigquery.Client(credentials=self.auth.credentials)
        return self._client

    def query(self, query: str, to_dataframe: bool = True, **job_config_kwargs):
        # Submit
        job_config = google.cloud.bigquery.QueryJobConfig(**job_config_kwargs)
        query_job = self.client.query(query, job_config=job_config)

        # Return
        if job_config.dry_run:
            print(f"This query will process {query_job.total_bytes_processed:,} bytes")
            return query_job

        if to_dataframe:
            # Use the storage API if it's installed, else use REST. Google's default for this variable is 'True'.
            create_bqstorage_client = self._bigquery_storage_is_installed()
            # The default (True) will always work, Google will just raise a warning and fall back to REST
            # if the library isn't installed. But, we'll avoid the warning since this is a convenience
            # wrapper that is expected to just work. We don't ever instruct users to install the storage API,
            # so the warning can be confusing here.
            return query_job.to_dataframe(create_bqstorage_client=create_bqstorage_client)

        return query_job

    def list_table_names(self, dataset: str, project_id: str | None = None) -> list[str]:
        project = project_id or self.auth.GOOGLE_CLOUD_PROJECT
        return [tbl.table_id for tbl in self.client.list_tables(f"{project}.{dataset}")]

    @staticmethod
    def _bigquery_storage_is_installed() -> bool:
        """Check whether ``google.cloud.bigquery_storage`` is installed by trying to import it.

        Returns:
            bool:
                False if the import causes ModuleNotFoundError, else True.
        """
        try:
            import google.cloud.bigquery_storage
        except ModuleNotFoundError:
            return False
        return True


@attrs.define
class Table:
    """Methods and properties for interacting with a Google BigQuery table.

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
    _client: Client | google.cloud.bigquery.Client | None = attrs.field(
        default=None,
        validator=attrs.validators.optional(
            attrs.validators.instance_of((Client, google.cloud.bigquery.Client))
        ),
    )
    _table: google.cloud.bigquery.Table | None = attrs.field(default=None, init=False)
    _schema: Optional["pd.DataFrame"] = attrs.field(default=None, init=False)

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

    def __getattr__(self, attr):
        """If ``attr`` doesn't exist in this class, try getting it from the underlying ``google.cloud.bigquery.Table``.

        Raises:
            AttributeError:
                if ``attr`` doesn't exist in either the pittgoogle or google.cloud API.
        """
        try:
            return getattr(self.table, attr)
        except AttributeError as excep:
            msg = f"Neither 'pittgoogle.bigquery.Table' nor 'google.cloud.bigquery.Table' has attribute '{attr}'"
            raise AttributeError(msg) from excep

    @property
    def auth(self) -> Auth:
        """Credentials for the Google Cloud project that owns this table.

        This will be created using environment variables if necessary.
        """
        if self._auth is None:
            self._auth = Auth()
        return self._auth

    @property
    def id(self) -> str:
        """Fully qualified table ID with syntax 'projectid.dataset_name.table_name'."""
        return f"{self.projectid}.{self.dataset}.{self.name}"

    @property
    def projectid(self) -> str:
        """The table owner's Google Cloud project ID.

        Defaults to :attr:`Table.auth.GOOGLE_CLOUD_PROJECT`.
        """
        if self._projectid is None:
            self._projectid = self.auth.GOOGLE_CLOUD_PROJECT
        return self._projectid

    @property
    def table(self) -> google.cloud.bigquery.Table:
        """Google Cloud BigQuery Table object.

        Makes a `get_table` request if necessary.

        Returns:
            google.cloud.bigquery.Table:
                The BigQuery Table object, connected to the Cloud resource.
        """
        if self._table is None:
            self._table = self.client.get_table(self.id)
        return self._table

    @property
    def client(self) -> Client | google.cloud.bigquery.Client:
        """BigQuery Client used to access the table.

        This will be created using :attr:`Table.auth` if necessary.

        Returns:
            Client or google.cloud.bigquery.Client:
                The BigQuery client instance.
        """
        if self._client is None:
            self._client = Client(auth=self.auth)
        return self._client

    @property
    def schema(self) -> "pd.DataFrame":
        """Schema of the BigQuery table."""
        if self._schema is None:
            # [TODO] Wondering, should we avoid pandas here? Maybe make this a dict instead?
            import pandas as pd  # always lazy-load pandas. it hogs memory on cloud functions and run

            fields = []
            for field in self.table.schema:
                fld = field.to_api_repr()  # dict

                child_fields = fld.pop("fields", [])
                # Append parent field name so that the child field name has the syntax 'parent_name.child_name'.
                # This is the syntax that should be used in SQL queries and also the one shown on BigQuery Console page.
                [cfld.update(name=f"{fld['name']}.{cfld['name']}") for cfld in child_fields]

                fields.extend([fld] + child_fields)
            self._schema = pd.DataFrame(fields)

        return self._schema

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

    def query(
        self,
        *,
        columns: list[str] | None = None,
        where: str | None = None,
        limit: int | str | None = None,
        to_dataframe: bool = True,
        dry_run: bool = False,
        sql_only: bool = False,
    ):
        # We could use parameterized queries, but accounting for all input possibilities would take a good amount of
        # work which should not be necessary. This query will be executed with the user's credentials/permissions.
        # No special access is added here. The user can already submit arbitrary SQL queries using 'Table.client.query',
        # so there's no point in trying to protect against SQL injection here.

        # Construct the SQL statement
        sql = f"SELECT {', '.join(columns) if columns else '*'}"
        sql += f" FROM `{self.table.full_table_id.replace(':', '.')}`"
        if where is not None:
            sql += f" WHERE {where}"
        if limit is not None:
            sql += f" LIMIT {limit}"
        if sql_only:
            return sql

        return self.client.query(query=sql, dry_run=dry_run, to_dataframe=to_dataframe)
