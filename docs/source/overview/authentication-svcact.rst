..
    This file is intended to be included in authentication.rst

.. _service account:

Service Account (Recommended)
--------------------------------

These are instructions to create a service account and download a key file that can be
used for authentication.

#.  Prerequisite: Access to a Google Cloud :doc:`project <projects>`.

#.  Follow Google's instructions to
    `create a service account <https://cloud.google.com/docs/authentication/getting-started#creating_a_service_account>`__
    (ignore the other sections on that page).
    You will:

    -   Create a service account with the **Project > Owner** role.

    -   Download a key file that contains authorization credentials.
        **Keep this file secret!**

#.  Take note of the path to the key file you downloaded. Then,
    :ref:`set both environment variables <set env vars>`.

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
