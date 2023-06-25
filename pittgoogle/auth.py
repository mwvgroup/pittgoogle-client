#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""A class to handle authentication with Google Cloud."""
import logging
import os
from typing import TYPE_CHECKING, Union

import attrs
from google import auth as gauth
from google_auth_oauthlib.helpers import credentials_from_session
from requests_oauthlib import OAuth2Session

if TYPE_CHECKING:
    import google
    import requests_oauthlib


LOGGER = logging.getLogger(__name__)


@attrs.define
class Auth:
    """Credentials for authentication to a Google Cloud project.

    Missing parameters will be obtained from an environment variable of the same name,
    if it exists.

    :param GOOGLE_CLOUD_PROJECT:
        Project ID of the Google Cloud project to connect to.

    :param GOOGLE_APPLICATION_CREDENTIALS:
        Path to a keyfile containing service account credentials.
        Either this or both `OAUTH_CLIENT_*` settings are required for successful
        authentication using `Auth`.

    :param OAUTH_CLIENT_ID:
        Client ID for an OAuth2 connection.
        Either this and `OAUTH_CLIENT_SECRET`, or the `GOOGLE_APPLICATION_CREDENTIALS`
        setting, are required for successful authentication using `Auth`.

    :param OAUTH_CLIENT_SECRET:
        Client secret for an OAuth2 connection.
        Either this and `OAUTH_CLIENT_ID`, or the `GOOGLE_APPLICATION_CREDENTIALS` setting,
        are required for successful authentication using `Auth`.
    """

    GOOGLE_CLOUD_PROJECT = attrs.field(factory=lambda: os.getenv("GOOGLE_CLOUD_PROJECT", None))
    GOOGLE_APPLICATION_CREDENTIALS = attrs.field(
        factory=lambda: os.getenv("GOOGLE_APPLICATION_CREDENTIALS", None)
    )
    OAUTH_CLIENT_ID = attrs.field(factory=lambda: os.getenv("OAUTH_CLIENT_ID", None))
    OAUTH_CLIENT_SECRET = attrs.field(factory=lambda: os.getenv("OAUTH_CLIENT_SECRET", None))
    _credentials = attrs.field(default=None, init=False)
    _oauth2 = attrs.field(default=None, init=False)

    # credentials
    @property
    def credentials(
        self,
    ) -> Union["google.auth.credentials.Credentials", "google.oauth2.credentials.Credentials"]:
        """Credentials, loaded from a service account key file or an OAuth2 session."""
        if self._credentials is None:
            self._credentials = self.get_credentials()
        return self._credentials

    @credentials.setter
    def credentials(self, value):
        self._credentials = value

    @credentials.deleter
    def credentials(self):
        self._credentials = None

    def get_credentials(
        self,
    ) -> Union["google.auth.credentials.Credentials", "google.oauth2.credentials.Credentials"]:
        """Load user credentials from a service account key file or an OAuth2 session.

        Try the service account first, fall back to OAuth2.
        """
        # service account credentials
        try:
            credentials, project = gauth.load_credentials_from_file(
                self.GOOGLE_APPLICATION_CREDENTIALS
            )

        # OAuth2
        except (TypeError, gauth.exceptions.DefaultCredentialsError) as ekeyfile:
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
                credentials = credentials_from_session(self.oauth2)

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

    # OAuth2Session
    @property
    def oauth2(self) -> "requests_oauthlib.OAuth2Session":
        """`requests_oauthlib.OAuth2Session` connected to the Google Cloud project."""
        if self._oauth2 is None:
            self._oauth2 = self.authenticate_with_oauth2()
        return self._oauth2

    @oauth2.setter
    def oauth2(self, value):
        self._oauth2 = value

    @oauth2.deleter
    def oauth2(self):
        self._oauth2 = None

    def authenticate_with_oauth2(self) -> "requests_oauthlib.OAuth2Session":
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
        authorization_url, state = oauth2.authorization_url(
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
