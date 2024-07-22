# -*- coding: UTF-8 -*-
"""Classes to manage authentication with Google Cloud.

.. note::

    To authenticate, you must have completed one of the setup options described in
    :doc:`/one-time-setup/authentication`. The recommendation is to use a
    :ref:`service account <service account>` and :ref:`set environment variables <set env vars>`.
    In that case, you will not need to call this module directly.


.. autosummary::

    Auth

----
"""
import logging
import os

import attrs
import google.auth
import google.auth.credentials
import google.oauth2.credentials
import google_auth_oauthlib.helpers
from requests_oauthlib import OAuth2Session

LOGGER = logging.getLogger(__name__)


@attrs.define
class Auth:
    """Credentials for authenticating with a Google Cloud project.

    This class provides methods to load credentials from either a service account key file or an
    OAuth2 session. To authenticate, you must have completed one of the setup options described
    in :doc:`/one-time-setup/authentication`.

    In typical use cases, the following arguments are set as environment variables instead of
    being passed to `Auth` explicitly.

    Args:
        GOOGLE_CLOUD_PROJECT (str, optional):
            The project ID of the Google Cloud project to connect to.

        GOOGLE_APPLICATION_CREDENTIALS (str, optional):
            The path to a keyfile containing service account credentials. Either this or the
            `OAUTH_CLIENT_*` settings are required for successful authentication.

        OAUTH_CLIENT_ID (str, optional):
            The client ID for an OAuth2 connection. Either this and `OAUTH_CLIENT_SECRET`, or
            the `GOOGLE_APPLICATION_CREDENTIALS` setting, are required for successful
            authentication.

        OAUTH_CLIENT_SECRET (str, optional):
            The client secret for an OAuth2 connection. Either this and `OAUTH_CLIENT_ID`, or
            the `GOOGLE_APPLICATION_CREDENTIALS` setting, are required for successful
            authentication.

    Example:

        The basic call is:

        .. code-block:: python

            myauth = pittgoogle.Auth()

        This will load authentication settings from your :ref:`environment variables <set env vars>`.
        You can override this behavior with keyword arguments. This does not automatically load the
        credentials. To do that, request them explicitly:

        .. code-block:: python

            myauth.credentials

        It will first look for a service account key file, then fallback to OAuth2.

    ----
    """

    # Strings _below_ the field will make these also show up as individual properties in rendered docs.
    GOOGLE_CLOUD_PROJECT: str | None = attrs.field(
        factory=lambda: os.getenv("GOOGLE_CLOUD_PROJECT", None)
    )
    """The project ID of the Google Cloud project to connect to."""
    GOOGLE_APPLICATION_CREDENTIALS: str | None = attrs.field(
        factory=lambda: os.getenv("GOOGLE_APPLICATION_CREDENTIALS", None)
    )
    """The path to a keyfile containing service account credentials."""
    OAUTH_CLIENT_ID: str | None = attrs.field(factory=lambda: os.getenv("OAUTH_CLIENT_ID", None))
    """The client ID for an OAuth2 connection."""
    OAUTH_CLIENT_SECRET: str | None = attrs.field(
        factory=lambda: os.getenv("OAUTH_CLIENT_SECRET", None)
    )
    """The client secret for an OAuth2 connection."""
    # The rest don't need string descriptions because they are explicitly defined as properties below.
    _credentials = attrs.field(default=None, init=False)
    _oauth2 = attrs.field(default=None, init=False)

    @property
    def credentials(
        self,
    ) -> google.auth.credentials.Credentials | google.oauth2.credentials.Credentials:
        """Credentials, loaded from a service account key file or an OAuth2 session."""
        if self._credentials is None:
            self._credentials = self._get_credentials()
        return self._credentials

    def _get_credentials(
        self,
    ) -> google.auth.credentials.Credentials | google.oauth2.credentials.Credentials:
        """Load user credentials from a service account key file or an OAuth2 session.

        Try the service account first, fall back to OAuth2.
        """
        # service account credentials
        try:
            credentials, project = google.auth.load_credentials_from_file(
                self.GOOGLE_APPLICATION_CREDENTIALS
            )

        # OAuth2
        except (TypeError, google.auth.exceptions.DefaultCredentialsError) as ekeyfile:
            LOGGER.warning(
                (
                    "Service account credentials not found for "
                    f"\nGOOGLE_CLOUD_PROJECT {self.GOOGLE_CLOUD_PROJECT} "
                    f"\nGOOGLE_APPLICATION_CREDENTIALS {self.GOOGLE_APPLICATION_CREDENTIALS}"
                    "\nFalling back to OAuth2. "
                    "If this is unexpected, check the kwargs you passed or "
                    "try setting environment variables."
                )
            )
            try:
                credentials = google_auth_oauthlib.helpers.credentials_from_session(self.oauth2)

            except Exception as eoauth:
                raise PermissionError("Cannot obtain credentials.") from Exception(
                    [ekeyfile, eoauth]
                )

        else:
            if project != self.GOOGLE_CLOUD_PROJECT:
                # prevent confusion about which project we'll connect to
                raise ValueError(
                    (
                        f"GOOGLE_CLOUD_PROJECT ({self.GOOGLE_CLOUD_PROJECT}) "
                        "must match the credentials in "
                        "GOOGLE_APPLICATION_CREDENTIALS at "
                        f"{self.GOOGLE_APPLICATION_CREDENTIALS} (project: {project})."
                    )
                )

        LOGGER.info(f"Authenticated to Google Cloud project {self.GOOGLE_CLOUD_PROJECT}")

        return credentials

    @property
    def oauth2(self) -> OAuth2Session:
        """`requests_oauthlib.OAuth2Session` connected to the Google Cloud project."""
        if self._oauth2 is None:
            self._oauth2 = self._authenticate_with_oauth2()
        return self._oauth2

    def _authenticate_with_oauth2(self) -> OAuth2Session:
        """Guide user through authentication and create `OAuth2Session` for credentials.

        The user will need to visit a URL, authenticate themselves, and authorize
        `PittGoogleConsumer` to make API calls on their behalf.

        The user must have a Google account that is authorized make API calls
        through the project defined by `GOOGLE_CLOUD_PROJECT`.
        In addition, the user must be registered with Pitt-Google (this is a Google
        requirement on apps that are still in dev).
        """
        # create an OAuth2Session
        client_id = self.OAUTH_CLIENT_ID
        client_secret = self.OAUTH_CLIENT_SECRET
        authorization_base_url = "https://accounts.google.com/o/oauth2/auth"
        redirect_uri = "https://ardent-cycling-243415.appspot.com/"  # TODO: better page
        scopes = [
            "https://www.googleapis.com/auth/logging.write",
            "https://www.googleapis.com/auth/pubsub",
        ]
        oauth2 = OAuth2Session(client_id, redirect_uri=redirect_uri, scope=scopes)

        # instruct the user to authorize
        authorization_url, _ = oauth2.authorization_url(
            authorization_base_url,
            access_type="offline",
            # access_type="online",
            # prompt="select_account",
        )
        print(
            (
                "Please visit this URL to authenticate yourself and authorize "
                "PittGoogleConsumer to make API calls on your behalf:"
                f"\n\n{authorization_url}\n"
            )
        )
        authorization_response = input(
            "After authorization, you should be directed to the Pitt-Google Alert "
            "Broker home page. Enter the full URL of that page (it should start with "
            "https://ardent-cycling-243415.appspot.com/):\n"
        )

        # complete the authentication
        _ = oauth2.fetch_token(
            "https://accounts.google.com/o/oauth2/token",
            authorization_response=authorization_response,
            client_secret=client_secret,
        )
        LOGGER.info(f"Authenticated to Google Cloud project {self.GOOGLE_CLOUD_PROJECT}")

        return oauth2
