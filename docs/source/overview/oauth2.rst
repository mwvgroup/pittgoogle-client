OAuth2 Authentication
=====================

.. note::

	This should work, but it's cumbersome because it's only partially implemented.
	Consider using a :ref:`service account <service account>` instead.

.. contents::
   :local:
   :depth: 1

Requirements
-------------

#.  You must have a Google account (e.g., Gmail address) that is authorized make
    API calls through the project that is defined by the `GOOGLE_CLOUD_PROJECT`
    :ref:`environment variable <set env vars>`.

#.  You must be added to the list of authorized test users, and obtain the
    client ID and client secret. Contact us.
    (This is a Google requirement for apps in dev.)
	
    .. Include your Google account info (Gmail address).

#.  Unfortunately the pittgoogle-client does not yet store tokens, which means you will
    have to re-authenticate every time you make an API call.

Authentication Workflow
------------------------

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
