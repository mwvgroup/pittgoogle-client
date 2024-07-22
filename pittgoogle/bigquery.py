# -*- coding: UTF-8 -*-
"""Classes to facilitate connections to BigQuery datasets and tables.

.. autosummary::

    Client
    Table

----
"""
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

    ----
    """

    _auth: Auth = attrs.field(
        default=None, validator=attrs.validators.optional(attrs.validators.instance_of(Auth))
    )
    _client: google.cloud.bigquery.Client | None = attrs.field(default=None)

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
        """Google Cloud BigQuery client.

        If the client has not been initialized yet, it will be created using :attr:`Client.auth`.

        Returns:
            google.cloud.bigquery.Client:
                An instance of the Google Cloud BigQuery client.
        """
        if self._client is None:
            self._client = google.cloud.bigquery.Client(credentials=self.auth.credentials)
        return self._client

    def list_table_names(self, dataset: str, projectid: str | None = None) -> list[str]:
        """Get the names of the tables in the dataset.

        Args:
            dataset (str):
                The name of the dataset.
            projectid (str, optional):
                The dataset owner's Google Cloud project ID. If None,
                :attr:`Client.client.project` will be used.

        Returns:
            list[str]:
                A list of table names in the dataset.

        Example:

            .. code-block:: python

                bqclient = pittgoogle.bigquery.Client()
                bqclient.list_table_names(dataset="ztf", projectid=pittgoogle.ProjectIds().pittgoogle)
        """
        project = projectid or self.client.project
        return sorted([tbl.table_id for tbl in self.client.list_tables(f"{project}.{dataset}")])

    def query(
        self, query: str, to_dataframe: bool = True, to_dataframe_kwargs: dict | None = None, **job_config_kwargs
    ):
        """Submit a BigQuery query job.

        Args:
            query (str):
                The SQL query to execute.
            to_dataframe (bool, optional):
                Whether to fetch the results and return them as a pandas DataFrame (True, default) or
                just return the query job (False).
            to_dataframe_kwargs (dict, optional):
                Keyword arguments to be passed to ``google.cloud.bigquery.QueryJob.to_dataframe``.
                Notable options: ``dtypes`` (dict), ``max_results`` (int), ``create_bqstorage_client`` (bool).
                This is ignored unless ``to_dataframe`` is True.
                ``create_bqstorage_client`` controls whether to use `google.cloud.bigquery_storage` (True)
                or `google.cloud.bigquery` (False). `bigquery_storage` can be faster but is not necessary.
                If you do not specify this parameter, pittgoogle will set it to True if the `bigquery_storage`
                library is installed, else False.
            **job_config_kwargs:
                Keyword arguments to pass to the `google.cloud.bigquery.QueryJobConfig` constructor.
                Notable option: ``dry_run`` (bool).

        Returns:
            pandas.DataFrame if ``to_dataframe`` is True, else google.cloud.bigquery.QueryJob

        Example:

            Query two tables (ztf.alerts_v4_02 and ztf.alerts_v3_3) for data on one object (ZTF19acfixfe).

            .. code-block:: python

                bqclient = pittgoogle.bigquery.Client()
                pittgoogle_project = pittgoogle.ProjectIds().pittgoogle

                sql = f\"\"\"
                    SELECT objectId, candid, candidate.jd, candidate.fid, candidate.magpsf
                    FROM `{pittgoogle_project}.ztf.alerts_v3_3`
                    WHERE objectId = 'ZTF19acfixfe'
                    UNION ALL
                    SELECT objectId, candid, candidate.jd, candidate.fid, candidate.magpsf
                    FROM `{pittgoogle_project}.ztf.alerts_v4_02`
                    WHERE objectId = 'ZTF19acfixfe'
                \"\"\"

                diaobject_df = bqclient.query(query=sql)
        """
        # Submit
        job_config = google.cloud.bigquery.QueryJobConfig(**job_config_kwargs)
        query_job = self.client.query(query, job_config=job_config)

        # Return
        if job_config.dry_run:
            print(f"This query will process {query_job.total_bytes_processed:,} bytes")
            return query_job

        if to_dataframe:
            kwargs = to_dataframe_kwargs.copy() if to_dataframe_kwargs else {}
            # Google sets 'create_bqstorage_client' to True by default and then raises a warning if the
            # 'bigquery_storage' library is not installed. Most pittgoogle users are not likely to have
            # this installed or even know what it is. Let's avoid the warning and just quietly check for it.
            create_bqstorage_client = self._check_bqstorage_client(kwargs.pop("create_bqstorage_client", None))
            return query_job.to_dataframe(create_bqstorage_client=create_bqstorage_client, **kwargs)

        return query_job

    @staticmethod
    def _check_bqstorage_client(user_value: bool | None) -> bool:
        """If ``user_value`` is None, check whether ``google.cloud.bigquery_storage`` is installed by trying to import it.

        Returns:
            bool:
                ``user_value`` if it is not None. Else, True (False) if the import is (is not) successful.
        """
        if user_value is not None:
            return user_value

        try:
            import google.cloud.bigquery_storage  # noqa: W0611
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
            The table owner's Google Cloud project ID. If not provided, the client's project ID will be used.
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
    client: Client | None = attrs.field(factory=Client)
    """BigQuery client used to access the table."""
    # The rest don't need string descriptions because they are explicitly defined as properties below.
    _projectid: str = attrs.field(default=None)
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
        """Create a :class:`Table` object using a BigQuery client with implicit credentials.

        Use this method when creating a :class:`Table` object in code running in Google Cloud (e.g.,
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
        """
        if dataset is None:
            dataset = survey
        # if testid is not False, "False", or None, append it to the dataset
        if testid and testid != "False":
            dataset = f"{dataset}_{testid}"
        # create a client with implicit credentials
        client = Client(client=google.cloud.bigquery.Client())
        table = cls(name=name, dataset=dataset, projectid=client.project, client=client)
        # make the get request now to fail early if there's a problem
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
    def id(self) -> str:
        """Fully qualified table ID with syntax 'projectid.dataset.name'."""
        return f"{self.projectid}.{self.dataset}.{self.name}"

    @property
    def projectid(self) -> str:
        """The table owner's Google Cloud project ID.

        Defaults to :attr:`Table.client.client.project`.
        """
        if self._projectid is None:
            self._projectid = self.client.client.project
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
                # The dicts update in place.
                _ = [cfld.update(name=f"{fld['name']}.{cfld['name']}") for cfld in child_fields]

                fields.extend([fld] + child_fields)
            self._schema = pd.DataFrame(fields)

        return self._schema

    def insert_rows(self, rows: list[dict | Alert]) -> list[dict]:
        """Insert rows into the BigQuery table.

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
        return_sql: bool = False,
    ):
        """Submit a BigQuery query job. Against this table.

        This method supports basic queries against this table. For more complex queries or queries
        against multiple tables, use :attr:`Client.query`.

        Args:
            columns (list[str], optional):
                List of columns to select. If None, all columns are selected.
            where (str, optional):
                SQL WHERE clause.
            limit (int or str, optional):
                Maximum number of rows to return.
            to_dataframe (bool, optional):
                Whether to fetch the results and return them as a pandas DataFrame (True, default) or
                just return the query job (False).
            dry_run (bool, optional):
                Whether to do a dry-run only to check whether the query is valid and estimate costs.
            return_sql (bool, optional):
                If True, the SQL query string will be returned. The query job will not be submitted.

        Returns:
            pandas.DataFrame, google.cloud.bigquery.QueryJob, or str:
                The SQL query string if ``return_sql`` is True. Otherwise, the results in a DataFrame
                if ``to_dataframe`` is True, else the query job.

        Example:

            .. code-block:: python

                alerts_tbl = pittgoogle.Table(
                    name="alerts_v4_02", dataset="ztf", projectid=pittgoogle.ProjectIds().pittgoogle
                )
                columns = ["objectId", "candid", "candidate.jd", "candidate.fid", "candidate.magpsf"]
                where = "objectId IN ('ZTF18aarunfu', 'ZTF24aavyicb', 'ZTF24aavzkuf')"

                diaobjects_df = alerts_tbl.query(columns=columns, where=where)
        """
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
        if return_sql:
            return sql

        # Do the query
        return self.client.query(query=sql, dry_run=dry_run, to_dataframe=to_dataframe)
