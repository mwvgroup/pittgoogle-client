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

    # Pitt-Google's Google Cloud project ID for ZTF and LVK data
    ardent-cycling-243415

    # Pitt-Google's Google Cloud project ID for LSST and Gaia DR3 data
    pitt-alert-broker

For examples of how to use the information on this page, please see our :ref:`API Reference <api reference>` and `User Demos <https://github.com/mwvgroup/pittgoogle-user-demos/>`__ repo.

-------------------------

..
    Tables below use ':class: tight-table' so that longer blocks of text will wrap
    instead of rendering as a single line per row with a horizontal scroll bar.
    The class is defined in docs/source/_static/css/custom.css.

.. _data lsst:

Legacy Survey of Space and Time (LSST)
--------------------------------------

:ref:`LSST <survey lsst>` is an upcoming wide-field, optical survey that is currently in the commissioning phase and
producing a public alert stream that is suitable for testing and development. The expected alert rate based on
pre-survey analysis is about 10^7 alerts per night.

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
        original alert data are converted into representations that can be safely serialized to JSON (e.g., ``NaN →
        None``, ``bytes →`` UTF-8 base64-encoded strings).

    * - lsst-lite
      - Lite version of lsst-alerts-json (every alert, subset of fields).

    * - lsst-xmatch
      - lsst-lite plus crossmatch results from Gaia's `vari_classifier_result` catalog.

    * - lsst-upsilon
      - lsst-lite plus UPSILoN's (Kim \& Bailer-Jones, 2015) multi-class classification results (e.g., RR Lyrae,
        Cepheid, Type II Cepheid, Delta Scuti star, eclipsing binary, long-period variable, etc.). Messages
        published to this topic contain the attributes: `pg_upsilon_x_label` and `pg_upsilon_x_flag` where "x" is
        either "u", "g", "r", "i", "z", or "y" (e.g., `pg_upsilon_u_label`; `pg_upsilon_u_flag`).

    * - lsst-variability
      - lsst-lite plus Stetson J indices for each band used to observe the diaObject associated with an alert.
        Messages published to this topic contain the attribute: `pg_variable`. The value of this Pub/Sub message
        attribute is set to "likely" if the alert has a Stetson J index of at least 20 and at least 30 detections in
        the g, r, or u band. The default value is "unlikely".

    * - lsst-supernnova
      - lsst-lite plus SuperNNova classification results (Ia vs non-Ia).

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
      - alerts_v11_1
      - Alert data for LSST schema version 11.1. This table is an archive of the lsst-alerts Pub/Sub stream,
        excluding image cutouts and metadata. It has the same schema as the original alert bytes (except cutouts),
        including nested and repeated fields. The fields `kafkaPublishTimestamp` and `healpix9`, `healpix19`, and
        `healpix29` are included to support time-based partitioning and spatial clustering, respectively.
        Equivalent tables exist for previous schema versions: alerts_v10_0 and alerts_v11_0.

    * - lsst
      - xmatch
      - Results from the lsst-xmatch module. This table identifies the three closest sources from the Gaia
        `vari_classifier_result` catalog within a 1 arcsecond radius from the `diaObject` in the alert packet. The field
        `kafkaPublishTimestamp` is included to support time-based partitioning.

    * - lsst
      - upsilon
      - Results from UPSILoN's (Kim \& Bailer-Jones, 2015) multi-class classification results (e.g., RR Lyrae,
        Cepheid, Type II Cepheid, Delta Scuti star, eclipsing binary, long-period variable, etc.). Contains
        the predicted label (i.e., class), the probability of the predicted label, and a flag value: 0
        (successful classification), 1 (suspicious classification because the period is in period alias or the period
        SNR is lower than 20) for each band used to observe the diaObject associated with an alert. The field
        `kafkaPublishTimestamp` is included to support time-based partitioning.

    * - lsst
      - variability
      - Results from the lsst-variability module. This table contains Stetson J indices and the number of detections (i.e.,
        data points) for each band used to observe the diaObject associated with an alert. The field
        `kafkaPublishTimestamp` is included to support time-based partitioning.

    * - lsst
      - supernnova
      - Results from a SuperNNova (Möller \& de Boissière, 2019) Type Ia supernova classification (binary). The field
        `kafkaPublishTimestamp` is included to support time-based partitioning.

Cloud Storage Buckets
^^^^^^^^^^^^^^^^^^^^^

.. list-table::
    :class: tight-table
    :widths: 40 60
    :header-rows: 1

    * - Bucket
      - Description

    * - pitt-alert-broker-lsst_alerts
      - Alert data for LSST. This bucket is an Avro file archive of the lsst-alerts Pub/Sub stream,
        including image cutouts and metadata. Each alert is stored as a separate Avro file.
        The filename syntax is: `<schema_version>/kafkaPublishTimestamp=<kafka_timestamp>/<objectid_key>=<objectid>/<sourceid_key>=<sourceid>.avro`.
        DIA Object example: `v10_0/kafkaPublishTimestamp=2026-02-25/diaObjectId=3516505565058564097/diaSourceId=3527242976319242284.avro`.
        Solar System Object example: `v10_0/kafkaPublishTimestamp=2026-02-25/ssObjectId=3516505565058564097/diaSourceId=3527242976319242284.avro`.

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

.. _data gaia:

Gaia Space Observatory (Gaia)
--------------------------------------

:ref:`Gaia <survey gaia>` is a retired space observatory that has made more than three trillion observations of two billion stars and other objects throughout the Milky Way galaxy and beyond from 27 July 2014 to 15 January 2025.
All of the Gaia data products presented here are products of Gaia Data Release 3.

BigQuery Tables
^^^^^^^^^^^^^^^

.. list-table::
    :class: tight-table
    :widths: 15 15 70
    :header-rows: 1

    * - Dataset
      - Table
      - Description

    * - xmatch_gaia
      - agn
      - Information on AGN properties.

    * - xmatch_gaia
      - cepheid
      - Information of Cepheid stars.

    * - xmatch_gaia
      - classifier_result
      - Variability classification results of all variable source classifiers.

    * - xmatch_gaia
      - compact_companion
      - Information on compact companion candidates.

    * - xmatch_gaia
      - eclipsing_binaries
      - Properties of eclipsing binaries resulting from the variability analysis.

    * - xmatch_gaia
      - epoch_radial_velocity
      - Epoch radial velocity data points for a sub-set of variable stars.

    * - xmatch_gaia
      - long_period_variable
      - Information on Long Period Variable stars.

    * - xmatch_gaia
      - microlensing
      - Information on microlensing events.

    * - xmatch_gaia
      - ms_oscillator
      - Information on main-sequence oscillators.

    * - xmatch_gaia
      - planetary_transit
      - Candidate planetary transit events. This is the table that replaced the original dataset published on 13 June 2022 as part of Gaia DR3 which was found to contain serious errors.

    * - xmatch_gaia
      - rad_vel_statistics
      - Statistical parameters of radial velocity time series.

    * - xmatch_gaia
      - rotation_modulation
      - information on solar-like stars with rotational modulation.

    * - xmatch_gaia
      - rrlyrae
      - Information on RR Lyrae stars.

    * - xmatch_gaia
      - short_timescale
      - Information on short-timescale variable sources.
