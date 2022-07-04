Usage
-----

You must obtain credentials before making API calls.
There are two options:

#.  :ref:`service account` (recommended)

#.  :doc:`/overview/oauth2`

This example uses a service account.

The basic call is:

.. code-block:: python

    from pittgoogle import auth

    myauth = auth.Auth(auth.AuthSettings())

As long as you have :ref:`set your environment variables <set env vars>`,
`AuthSettings` will find your credentials.

However, we still don't know if they are valid.
To authenticate, request the `credentials` explicitly:

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
