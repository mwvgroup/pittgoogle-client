..
    This is the main page
    the file is intended to be included in index.rst

Pitt-Google Broker
==============================================

The Pitt-Google Broker is a cloud-based alert distribution service designed to provide near real-time processing of data from large-scale astronomical surveys like the `Legacy Survey of Space and Time <https://www.lsst.org/>`_ (LSST). LSST will deliver on order a million real-time alerts each night providing information on astronomical targets within 60 seconds of observation. The Pitt-Google Broker is a scalable broker system being designed to maximize the availability and usefulness of the LSST alert data by combining cloud-based analysis opportunities with value-added data products.

The Pitt-Google Broker runs on the `Google Cloud Platform <https://cloud.google.com/>`_ (GCP) and is currently focused on processing and serving alerts from the `Zwicky Transient Facility <https://www.ztf.caltech.edu/>`_ (ZTF), and extending broker capabilities using ZTF, the LSST Alert Simulator, and the DECam Alliance for Transients (DECAT) stream.

**Initial setup** for data access requires 2 steps:

#.  :ref:`install`

#.  :ref:`Authenticate to Google Cloud <authentication>`

If you run into trouble, please
`open an Issue <https://github.com/mwvgroup/pittgoogle-client/issues>`__.

**Data overview**

.. manual list so index.rst renders correctly
.. toctree::
    :maxdepth: 1
    :hidden:

    data-pubsub
    data-bigquery
    data-cloud-storage

-   :ref:`data pubsub`

-   :ref:`data bigquery`

-   :ref:`data cloud storage`
