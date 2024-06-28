.. Pitt-Google Broker documentation master file, created by
   sphinx-quickstart on Wed Jul 28 17:34:03 2021.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

.. toctree::
    :maxdepth: 3
    :hidden:

    main/listing
    Install<main/one-time-setup/install>
    main/one-time-setup/index
    main/faq/index

.. toctree::
    :caption: For Developers
    :maxdepth: 3
    :hidden:

    for-developers/setup-environment

.. toctree::
    :caption: API Reference
    :maxdepth: 3
    :hidden:

    api-reference/alert
    api-reference/auth
    api-reference/bigquery
    api-reference/exceptions
    api-reference/pubsub
    api-reference/registry
    api-reference/types
    api-reference/utils

pittgoogle-client
==============================================

`pittgoogle-client` is a python library that facilitates access to astronomy data that lives in Google Cloud services.
It is being developed  the `Pitt-Google alert broker <https://github.com/mwvgroup/Pitt-Google-Broker>`__ is curated and maintained  available in Google Cloud.

**Initial setup** for data access requires 2 steps:

#.  :ref:`install`

#.  :ref:`Authenticate to Google Cloud <authentication>`

If you run into trouble, please
`open an Issue <https://github.com/mwvgroup/pittgoogle-client/issues>`__.
