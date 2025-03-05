.. _listings:

Data Listings
=============

This page contains a listing of all data products served by Pitt-Google Alert Broker and includes the connection information needed for access.

.. contents:: Jump to:
    :depth: 1
    :local:

All data is served through public data repositories in Google Cloud.
Pitt-Google's Google Cloud project ID, which will be needed for access, is:

.. code-block::

    # Pitt-Google's Google Cloud project ID
    ardent-cycling-243415

For examples of how to use the information on this page, please see our :ref:`API Reference <api reference>` and `User Demos <https://github.com/mwvgroup/pittgoogle-user-demos/>`__ repo.

-------------------------

..
    Tables below use ':class: tight-table' so that longer blocks of text will wrap
    instead of rendering as a single line per row with a horizontal scroll bar.
    The class is defined in docs/source/_static/css/custom.css.

.. _data ztf:

Zwicky Transient Facility (ZTF)
-------------------------------

:ref:`ZTF <survey ztf>` is a wide-field, optical survey producing an alert stream at a rate of 10^5 - 10^6 per night.

Pub/Sub Alert Streams
^^^^^^^^^^^^^^^^^^^^^

.. list-table::
    :class: tight-table
    :widths: 25 75
    :header-rows: 1

    * - Topic
      - Description

    * - .. centered:: *Data Streams*
      -

    * - ztf-alerts
      - ZTF alert stream in Pub/Sub, cleaned of duplicate alerts.
        Messages contain the original alert bytes and metadata.

    * - ztf-lite
      - Lite version of ztf-alerts (every alert, subset of fields).

    * - ztf-tagged
      - ztf-lite with basic categorizations such as "is pure" and “is likely extragalactic
        transient” added to the message metadata to aid filtering.

    * - ztf-SuperNNova
      - ztf-tagged plus SuperNNova classification results (Ia vs non-Ia).

    * - .. centered:: *Notification Streams*
      -

    * - ztf-alert_avros
      - One message per alert indicating that the Avro file is available in a Cloud Storage bucket.
        The file and bucket names are in the message attributes. Messages contain no data.

    * - .. centered:: *Testing Stream*
      -

    * - ztf-loop
      - Recent messages from the ztf-alerts stream, published at a rate of 1 per second.
        This stream is intended for testing and development use cases.

BigQuery Tables
^^^^^^^^^^^^^^^

.. list-table::
    :class: tight-table
    :widths: 15 15 70
    :header-rows: 1

    * - Dataset
      - Table
      - Description

    * - ztf
      - alerts_v4_02
      - Alert data for ZTF schema version 4.02. This table is an archive of the ztf-alerts Pub/Sub stream,
        excluding image cutouts and metadata.
        It has the same schema as the original alert bytes (except cutouts), including nested and repeated fields.
        Equivalent tables exist for previous schema versions: alerts_v3_3,  alerts_v3_1,  alerts_v3_0,  alerts_v1_8.

    * - ztf
      - DIASource
      - ZTF alert data of the DIA source that triggered the alert. Includes the object ID and a
        list of source IDs for the previous sources included in the alert, excluding cutouts and
        data for previous sources. The schema is flat.

    * - ztf
      - SuperNNova
      - Results from a SuperNNova (Möller \& de Boissière, 2019)
        Type Ia supernova classification (binary).

Cloud Storage Buckets
^^^^^^^^^^^^^^^^^^^^^

.. list-table::
    :class: tight-table
    :widths: 40 60
    :header-rows: 1

    * - Bucket
      - Description

    * - ardent-cycling-243415-ztf_alerts_v4_02
      - Alert data for ZTF schema version 4.02. This bucket is an Avro file archive of the ztf-alerts Pub/Sub stream,
        including image cutouts and metadata. Each alert is stored as a separate Avro file.
        The filename syntax is: `<ztf_topic>/<objectId>/<candid>.avro`.
        Equivalent buckets exist for previous schema versions: v3_3,  v3_1,  v3_0,  v1_8.

.. _data lvk:

LIGO-Virgo-KAGRA (LVK)
-------------------------------

:ref:`LVK <survey lvk>` is a gravitational wave collaboration producing an alert stream at a rate of 50 - 100 per day.

Pub/Sub Alert Streams
^^^^^^^^^^^^^^^^^^^^^

.. list-table::
    :class: tight-table
    :widths: 25 75
    :header-rows: 1

    * - Topic
      - Description

    * - .. centered:: *Data Streams*
      -

    * - lvk-alerts
      - LVK alert stream in Pub/Sub.
        Messages contain the original alert bytes and metadata.

BigQuery Tables
^^^^^^^^^^^^^^^

.. list-table::
    :class: tight-table
    :widths: 15 15 70
    :header-rows: 1

    * - Dataset
      - Table
      - Description

    * - lvk
      - alerts_v1_0
      - Alert data from the LVK O4 observing run. This table is an archive of the lvk-alerts Pub/Sub stream.
        It has the same schema as the original alert bytes, including nested and repeated fields.

Legacy Survey of Space and Time (LSST)
-------------------------------

:ref:`LSST <survey lsst>` is a wide-field, optical survey producing an alert stream at an average rate of 10^7 per night.

Pub/Sub Alert Streams
^^^^^^^^^^^^^^^^^^^^^

.. list-table::
    :class: tight-table
    :widths: 25 75
    :header-rows: 1

    * - Topic
      - Description

    * - .. centered:: *Data Streams*
      -

    * - lsst-alerts
      - LSST alert stream in Pub/Sub, cleaned of duplicate alerts.
        Messages contain the original alert bytes and metadata.

BigQuery Tables
^^^^^^^^^^^^^^^

.. list-table::
    :class: tight-table
    :widths: 15 15 70
    :header-rows: 1

    * - Dataset
      - Table
      - Description

    * - lsst
      - alerts_v7_4
      - Alert data for LSST schema version 7.4. This table is an archive of the lsst-alerts Pub/Sub stream,
        excluding image cutouts and metadata.
        It has the same schema as the original alert bytes (except cutouts), including nested and repeated fields.
        Equivalent tables exist for previous schema versions: alerts_v7_3,  alerts_v7_1.

Cloud Storage Buckets
^^^^^^^^^^^^^^^^^^^^^

.. list-table::
    :class: tight-table
    :widths: 40 60
    :header-rows: 1

    * - Bucket
      - Description

    * - ardent-cycling-243415-lsst_alerts
      - Alert data for LSST. This bucket is an Avro file archive of the lsst-alerts Pub/Sub stream,
        including image cutouts and metadata. Each alert is stored as a separate Avro file.
        The filename syntax is: `<schema_version>/<alert_date>/<diaObjectId>/<diaSourceId>.avro`.
        Equivalent directory structures exist for previous schema versions: v7_3,  v7_1.
