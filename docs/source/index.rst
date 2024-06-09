.. Pitt-Google Broker documentation master file, created by
   sphinx-quickstart on Wed Jul 28 17:34:03 2021.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

.. toctree::
    :maxdepth: 3
    :hidden:

    Install<overview/install>
    overview/authentication
    overview/project
    overview/env-vars
    overview/cost
    overview/adv-setup

.. toctree::
    :caption: Tutorials
    :maxdepth: 3
    :hidden:

    tutorials/bigquery
    tutorials/cloud-storage
    tutorials/ztf-figures

.. toctree::
    :caption: For Developers
    :maxdepth: 3
    :hidden:

    for-developers/setup-development-mode

.. toctree::
    :caption: API Reference
    :maxdepth: 3
    :hidden:

    api/auth
    api/bigquery
    api/pubsub
    api/utils

pittgoogle-client
==============================================

`pittgoogle-client` is a python library that facilitates access to astronomy data that lives in Google Cloud services.
It is being developed  the `Pitt-Google alert broker <https://github.com/mwvgroup/Pitt-Google-Broker>`__ is curated and maintained  available in Google Cloud.

**Initial setup** for data access requires 2 steps:

#.  :ref:`install`

#.  :ref:`Authenticate to Google Cloud <authentication>`

If you run into trouble, please
`open an Issue <https://github.com/mwvgroup/pittgoogle-client/issues>`__.

**Data overview**

.. _data pubsub:

Pub/Sub Message Streams
=======================

.. list-table:: Streams
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
==================

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

.. _data cloud storage:

Cloud Storage
====================

.. list-table:: Buckets
    :class: tight-table
    :widths: 40 60
    :header-rows: 1

    * - Bucket Name
      - Description

    * - ardent-cycling-243415-ztf-alert_avros
      - Contains the complete, original alert packets as Avro files.
        Filename syntax is: `<ztf_topic>/<objectId>/<candid>.avro`
