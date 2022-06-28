Cloud (File) Storage
====================

.. toctree::
    :maxdepth: 1
    :hidden:

    cloud-storage-tutorial

We store alert data in the
`Cloud Storage <https://cloud.google.com/storage/docs/introduction>`__
buckets listed below.

To learn how to access, see the

-   :doc:`cloud-storage-tutorial`

.. list-table:: Buckets
    :class: tight-table
    :widths: 40 60
    :header-rows: 1

    * - Bucket Name
      - Description

    * - ardent-cycling-243415-ztf-alert_avros
      - This bucket contains the complete, original alert packets as Avro files.
        The files are named using the syntax: {objectId}.{candid}.{ztf_topic}.avro
