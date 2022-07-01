.. _oauth2:

OAuth2
------------------------

These are instructions to complete authentication using OAuth2.

.. note::

	This works, but it's cumbersome because it's only partially implemented.
	Consider using a :ref:`service account <service account>` instead.

.. contents::
   :local:
   :depth: 1

Requirements
~~~~~~~~~~~~~~~

#.  You must have a Google account (e.g., Gmail address) that is authorized make
    API calls through the :ref:`project <projects>` that is defined by the `GOOGLE_CLOUD_PROJECT`
    :ref:`environment variable <set env vars>`.

#.  You must be added to the list of authorized test users, and obtain the
    client ID and client secret. Contact us.
    (This is a Google requirement for apps in dev.)

#.  You will have to re-authenticate every time you instantiate a new auth or client object.

Authentication Workflow
~~~~~~~~~~~~~~~~~~~~~~~~~~

#.  Set environment variables named
    `PITTGOOGLE_OAUTH_CLIENT_ID`` and `PITTGOOGLE_OAUTH_CLIENT_SECRET` to values
    obtained from Pitt-Google broker.

#.  Make an API call.

#.  The process will hang and ask you to visit a URL to complete authentication.
    Follow the instructions.

#.  Log in with the Google account attached to your project.

#.  Authorize the Pitt-Google app to make API calls on your behalf.
    This only needs to be done once for each API access scope
    (e.g., Pub/Sub, BigQuery, and Logging).

#.  Respond to the prompt on the command line by entering the full URL of the webpage
    you are redirected to after completing the above.
