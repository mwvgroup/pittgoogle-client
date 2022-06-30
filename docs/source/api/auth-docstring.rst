.. automodule:: pittgoogle.auth

Usage
-----

To use this module, you must have completed one of the setup options described in :doc:`/overview/authentication`.

In most cases you will not need to use this module directly.

The example below uses a service account.

The basic call is:

.. code-block:: python

    from pittgoogle import auth

    myauth = auth.Auth()

This will load authentication settings from your :ref:`environment variables <set env vars>`.

You can also send an instance of :mod:`AuthSettings()` or any of its attributes as keyword arguments.
Some examples:

.. code-block:: python

    myauth = auth.Auth(GOOGLE_CLOUD_PROJECT="kwarg-project-id")

    settings = auth.AuthSettings(
        GOOGLE_CLOUD_PROJECT="settings-project-id",
        GOOGLE_APPLICATION_CREDENTIALS="settings/path/to/key_file.json",
    )
    myauth = auth.Auth(settings)

    myauth = auth.Auth(settings, GOOGLE_CLOUD_PROJECT="kwarg-project-id")
    # the kwarg takes precedence, so myauth.GOOGLE_CLOUD_PROJECT = "kwarg-project-id"

This does not automatically load the credentials.
To do that, request them explicitly:

.. code-block:: python

    myauth.credentials

Classes
-------

`AuthSettings`
~~~~~~~~~~~~~~~~~~~

.. autoclass:: pittgoogle.auth.AuthSettings
   :members:
   :member-order: bysource


`Auth`
~~~~~~~~~~~~~~~~~~~

.. autoclass:: pittgoogle.auth.Auth
   :members:
   :member-order: bysource
