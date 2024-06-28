.. _authentication:

Authentication
================

Authentication for API calls is obtained directly from Google Cloud.
Two options are implemented in pittgoogle. Complete at least one:

- :ref:`Service Account (recommended) <service account>`
- :ref:`OAuth2 <oauth2>`

.. _service account:

Service Account
---------------

These are instructions to create a service account and download a key file that can be
used for authentication.

#.  Prerequisite: Access to a Google Cloud :ref:`project <projects>`.

#.  Follow Google's instructions to
    `create a service account <https://cloud.google.com/iam/docs/service-accounts-create#creating>`__.
    You will:

    -   Create a service account with the **Project > Owner** role.

    -   Download a key file that contains authorization credentials.
        **Keep this file secret!**

#.  Take note of the path to the key file you downloaded. Use it in the next step,
    :ref:`Set environment variables <set env vars>`.

.. note::

    The **Project > Owner** role gives the service account permission to do anything and
    everything, within the project.
    It is the simplest option and allows you to avoid the headache of tracking down
    "permission denied" errors.
    However, this role is excessively permissive in essentially all cases.
    If you want to restrict the permissions granted to the service account,
    assign a different role(s).
    A good place to look is:
    `Predefined roles <https://cloud.google.com/iam/docs/understanding-roles#predefined>`__.
