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

.. _data lsst:

Legacy Survey of Space and Time (LSST)
--------------------------------------

:ref:`LSST <survey lsst>` is an upcoming wide-field, optical survey that is currently in the commissioning phase and
producing an alert stream that is suitable for testing and development. LSST is expected to produce on average 10^7
alerts per night.

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
      - Avro serialized LSST alert stream in Pub/Sub, cleaned of duplicate alerts.
        Messages contain the original alert bytes and metadata.

    * - lsst-alerts-json
      - JSON-serialized LSST alert stream in Pub/Sub, cleaned of duplicate alerts. Non-JSON-serializable values in the
        original alert data are converted into representations that can be safely serialized to JSON. For example:
        - ``NaN -> None``
        -  ``bytes ->`` UTF-8 strings representing the base64-encoded byte values

    * - lsst-lite
      - Lite version of lsst-alerts-json (every alert, subset of fields).

    * - lsst-upsilon
      - lsst-lite plus UPSILoN's (Kim \& Bailer-Jones, 2015) classification (multi-class) of periodic variable stars
        (e.g., RR Lyraes, Cepheids, Type II Cepheids, Delta Scuti stars, eclipsing binaries, and long-period
        variables) and their subclasses for each band used to observe the source associated with an alert. Messages
        published to this topic contain the following attributes:
        - "pg_upsilon_x_label", where "x" specifies the data of the band used to classify the source (e.g., "u", "g",
          "r", "i", "z", "y").
        - "pg_upsilon_x_flag", where "x" specifies the data of the band used to classify the source (e.g., "u", "g",
          "r", "i", "z", "y").


    * - lsst-variability
      - lsst-lite plus the number of detections (i.e., data points) and the StetsonJ statistic for each band used to
        observe the source associated with an alert. Messages published to this topic contain the attribute:
        "pg_variable". The value of this Pub/Sub message attribute is set to "likely" if the alert has StetsonJ
        statistic values of at least 20 and at least 30 detections in the g, r, or u band. The default value is
        "unlikely".

BigQuery Tables
^^^^^^^^^^^^^^^

.. list-table::
    :class: tight-table
    :widths: 15 15 70
    :header-rows: 1

    * - Dataset
      - Table
      - Description

    * - lsst_alerts
      - alerts_v7_4
      - Alert data for LSST schema version 7.4. This table is an archive of the lsst-alerts Pub/Sub stream,
        excluding image cutouts and metadata.
        It has the same schema as the original alert bytes (except cutouts), including nested and repeated fields.
        Equivalent tables exist for previous schema versions: alerts_v7_3,  alerts_v7_1.

    * - lsst_value_added
      - upsilon
      - Results from UPSILoN's (Kim \& Bailer-Jones, 2015) classification (multi-class) of periodic variable
        stars (e.g., RR Lyraes, Cepheids, Type II Cepheids, Delta Scuti stars, eclipsing binaries, and long-period
        variables) and their subclasses for each band used to observe the source associated with an alert. Contains
        the predicted label (i.e., class) for each band, the probability of the predicted label, and a flag value (0 or
        1).
        - 0: Successful classification
        - 1: Suspicious classification because the period is in period alias or the period SNR is lower than 20

    * - lsst_value_added
      - variability
      - This table shows the number of detections (i.e., data points) and the StetsonJ statistic for each band used to
        observe the source associated with an alert.

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
        For example, `v7_3/2026-10-01/3516505565058564097/3527242976319242284.avro`.
