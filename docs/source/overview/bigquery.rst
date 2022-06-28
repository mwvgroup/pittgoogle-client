BigQuery Catalogs
==================

.. toctree::
    :maxdepth: 1
    :hidden:

    bigquery-tutorial

We store data in the `BigQuery <https://cloud.google.com/bigquery/docs/introduction>`__
datasets and tables described below.

To learn how to access, see the

-   :doc:`bigquery-tutorial`

-   :doc:`/api/bigquery` module documentation

.. list-table:: Datasets and Tables
    :class: tight-table
    :widths: 15 15 70
    :header-rows: 1

    * - Dataset
      - Table
      - Description

    * - ztf_alerts
      - alerts
      - Complete alert packet, excluding image cutouts.
        Same schema as the original alert, including nested and repeated fields.

    * - ztf_alerts
      - DIASource
      - Alert packet data for the triggering source only. Including the object ID and a
        list of source IDs for the previous sources included in the alert,
        excluding cutouts and data for previous sources.
        Flat schema.

    * - ztf_alerts
      - SuperNNova
      - Results from a SuperNNova (Möller \& de Boissière, 2019)
        Type Ia supernova classification (binary).

    * - ztf_alerts
      - metadata
      - Information recording Pitt-Google processing (e.g., message publish times,
        bucket name and filename, etc.).
