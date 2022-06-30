Pub/Sub Message Streams
=======================

.. list-table:: Streams
    :class: tight-table
    :widths: 25 75
    :header-rows: 1

    * - Topic
      - Description

    * - ztf-alerts
      - Full ZTF alert stream.

    * - ztf-exgalac_trans_cf
      - ZTF alert stream filtered for likely extragalactic transients.

    * - ztf-SuperNNova
      - SuperNNova classification results (Ia vs non-Ia) + alert contents for
        alerts that passed the likely-extragalactic-transients filter.

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
