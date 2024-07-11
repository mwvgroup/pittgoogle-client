.. _listings:

Data Listings
=============

This page contains a listing of all data products served by Pitt-Google Alert Broker along with the connection information needed for access.
The listings are organized by survey, then data product and format.

All data is served through Pitt-Google's public data repositories in Google Cloud.
Pitt-Google's Google Cloud project ID, which will be needed to access the data stores listed below, is:

.. code-block::

    # Pitt-Google's Google Cloud project ID
    ardent-cycling-243415

For examples of how to use the information on this page, please see our :ref:`API Reference <api reference>` and `User Demos <https://github.com/mwvgroup/pittgoogle-user-demos/>`__ repo.

.. _data ztf:

Zwicky Transient Facility (:ref:`ZTF <survey ztf>`)
---------------------------------------------------

ZTF is a wide-field, optical survey in three bands: r, g, and i.
It produces an alert stream of transients detected by difference imaging at a rate of 10^5 - 10^6 alerts per night.
It scans the entire Northern sky every two days.



ZTF Mission resources:

- `ZTF Homepage <https://www.ztf.caltech.edu/>`__
- `ZTF Science Data System Explanatory Supplement <https://irsa.ipac.caltech.edu/data/ZTF/docs/ztf_explanatory_supplement.pdf>`__

Pitt-Google Broker serves the ZTF alert data in the formats listed below.

Pub/Sub Message Streams
^^^^^^^^^^^^^^^^^^^^^^^

.. list-table:: Pitt-Google's ZTF Streams
    :class: tight-table
    :widths: 25 75
    :header-rows: 1

    * - Topic Name
      - Description

    * - **ztf-loop**
      - Use this stream for testing. Recent ZTF alerts are published to this topic
        at a roughly constant rate of 1 per second.

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


BigQuery Tables
^^^^^^^^^^^^^^^

.. list-table:: Pitt-Google's ZTF Datasets and Tables
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


Cloud Storage Files
^^^^^^^^^^^^^^^^^^^

.. list-table:: Pitt-Google's ZTF Buckets
    :class: tight-table
    :widths: 40 60
    :header-rows: 1

    * - Bucket Name
      - Description

    * - ardent-cycling-243415-ztf-alert_avros
      - Contains the complete, original alert packets as Avro files.
        Filename syntax is: `<ztf_topic>/<objectId>/<candid>.avro`
