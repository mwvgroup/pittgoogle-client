Data Listing
==============================================

This page contains a listing of the data resources served by Pitt-Google Alert Broker.

.. _data pubsub:

Pub/Sub Message Streams
------------------------

.. list-table:: ZTF Streams
    :class: tight-table
    :widths: 25 75
    :header-rows: 1

    * - Topic
      - Description

    * - ztf-alerts
      - Full ZTF alert stream

    * - ztf-lite
      - Lite version of ztf-alerts (every alert, subset of fields)

    * - ztf-tagged
      - ztf-lite with basic categorizations such as “is pure” and “is likely extragalactic
        transient” added to the message metadata.

    * - ztf-SuperNNova
      - ztf-tagged plus SuperNNova classification results (Ia vs non-Ia).

    * - ztf-alert_avros
      - Notification stream from the ztf-alert_avros Cloud Storage bucket indicating
        that a new alert packet is in file storage.
        These messages contain no data, only attributes.
        The file name is in the attribute "objectId",
        and the bucket name is in the attribute "bucketId".

    * - ztf-BigQuery
      - Notification stream indicating that alert data is available in BigQuery tables.

    * - **ztf-loop**
      - Use this stream for testing. Recent ZTF alerts are published to this topic
        at a roughly constant rate of 1 per second.

.. _data bigquery:

BigQuery Catalogs
------------------------

.. list-table:: ZTF Datasets and Tables
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

.. _data cloud storage:

Cloud Storage
------------------------

.. list-table:: ZTF Buckets
    :class: tight-table
    :widths: 40 60
    :header-rows: 1

    * - Bucket Name
      - Description

    * - ardent-cycling-243415-ztf-alert_avros
      - Contains the complete, original alert packets as Avro files.
        Filename syntax is: `<ztf_topic>/<objectId>/<candid>.avro`
