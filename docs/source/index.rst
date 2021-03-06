.. Pitt-Google Broker documentation master file, created by
   sphinx-quickstart on Wed Jul 28 17:34:03 2021.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Pitt-Google Broker
==============================================

The Pitt-Google Broker is a cloud-based alert distribution service designed to provide near real-time processing of data from large-scale astronomical surveys like the `Legacy Survey of Space and Time <https://www.lsst.org/>`_ (LSST). LSST will deliver on order a million real-time alerts each night providing information on astronomical targets within 60 seconds of observation. The Pitt-Google Broker is a scalable broker system being designed to maximize the availability and usefulness of the LSST alert data by combining cloud-based analysis opportunities with value-added data products.

The Pitt-Google Broker runs on the `Google Cloud Platform <https://cloud.google.com/>`_ (GCP) and is currently focused on processing and serving alerts from the `Zwicky Transient Facility <https://www.ztf.caltech.edu/>`_ (ZTF), and extending broker capabilities using ZTF, the LSST Alert Simulator, and the DECam Alliance for Transients (DECAT) stream.

.. .. toctree::
..    :hidden:
..
..    Overview<self>

.. toctree::
   :maxdepth: 2
   :caption: Access Data

   access-data/data-overview
   access-data/initial-setup
   access-data/bigquery
   access-data/cloud-storage
   access-data/pubsub

.. toctree::
   :hidden:
   :maxdepth: 1
   :caption: API Reference

   api/pittgoogle/bigquery
   api/pittgoogle/figures
   api/pittgoogle/pubsub
   api/pittgoogle/utils

..
.. Indices and tables
.. ==================
..
.. * :ref:`genindex`
.. * :ref:`modindex`
.. * :ref:`search`
