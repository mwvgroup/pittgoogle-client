..
    This is the docstring for the pittgoogle.auth module.
    The file is intended to be included in docs/source/api/auth.rst.

Usage
-----

.. note::

    To authenticate, you must have completed one of the setup options described in :doc:`/overview/authentication`.
    **The recommended workflow is to use a** :ref:`service account <service account>` **and** :ref:`set environment variables <set env vars>`.
    In that case, you will not need to call this module directly.


This example uses a service account.

The basic call is:

.. code-block:: python

    from pittgoogle import auth

    myauth = auth.Auth()

This will load authentication settings from your :ref:`environment variables <set env vars>`.
You can override this behavior with keyword arguments.

.. code-block:: python

    myauth = auth.Auth(
        GOOGLE_CLOUD_PROJECT="new-project-id",
        GOOGLE_APPLICATION_CREDENTIALS="new/path/to/GCP_auth_key.json"
    )

This does not automatically load the credentials.
To do that, request them explicitly:

.. code-block:: python

    myauth.credentials

It will first look for a service account key file, then fallback to OAuth2.

Classes
-------

`Auth`
~~~~~~~~~~~~~~~~~~~

.. autoclass:: pittgoogle.auth.Auth
   :members:
   :member-order: bysource
   :noindex:
