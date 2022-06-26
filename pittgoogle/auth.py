#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""Functions to facilitate authentication with Google Cloud."""

from dataclasses import asdict, dataclass, fields
import logging
import os

from google import auth as gauth
from google_auth_oauthlib.helpers import credentials_from_session
from requests_oauthlib import OAuth2Session
from typing import Optional, Union


LOGGER = logging.getLogger(__name__)


@dataclass
class AuthSettings:
    """Settings for authentication to Google Cloud.

    Any setting not provided during instantiation will be obtained from an environment
    variable of the same name, or None if this can't be found.

    GOOGLE_CLOUD_PROJECT:
        Project ID of the Google Cloud project to connect to.
    GOOGLE_APPLICATION_CREDENTIALS:
        Path to a keyfile containing service account credentials.
        Either this or both `OAUTH_CLIENT_` settings are required for successful
        authentication using `Auth`.
    OAUTH_CLIENT_ID:
        Client ID for an OAuth2 connection.
        Either this and `OAUTH_CLIENT_SECRET`, or the `GOOGLE_APPLICATION_CREDENTIALS`
        setting, are required for successful authentication using `Auth`.
    OAUTH_CLIENT_SECRET:
        Client secret for an OAuth2 connection.
        Either this and `OAUTH_CLIENT_ID`, or the `GOOGLE_APPLICATION_CREDENTIALS`
        setting, are required for successful authentication using `Auth`.
    """

    GOOGLE_CLOUD_PROJECT: str = os.getenv("GOOGLE_CLOUD_PROJECT")
    GOOGLE_APPLICATION_CREDENTIALS: Optional[str] = os.getenv(
        "GOOGLE_APPLICATION_CREDENTIALS", None
    )
    OAUTH_CLIENT_ID: Optional[str] = os.getenv("OAUTH_CLIENT_ID", None)
    OAUTH_CLIENT_SECRET: Optional[str] = os.getenv("OAUTH_CLIENT_SECRET", None)


@dataclass
class Auth:
    """Credentials and/or OAuth session for authentication to a Google Cloud project."""

    def __init__(self, settings: Union[AuthSettings, "Auth"]):
        """Attributes are created for each attribute of `AuthSettings`, if provided.

        Initialization is idempotent for caller convenience.

        The API call triggering authentication with Google Cloud is not made until
        the either the `credentials` or `session` attribute is explicitly requested.
        """
        # initialization should be idempotent
        # unpack auth settings to attributes
        for key, val in settings.__dict__.items():
            setattr(self, key, val)

        # initialize credentials but don't make a request for them
        self._credentials = getattr(self, "_credentials", None)
        self._oauth2 = getattr(self, "_oauth2", None)

    # credentials
    @property
    def credentials(self):
        """Credentials object."""
        if self._credentials is None:
            self._credentials = self.get_credentials()
        return self._credentials

    @credentials.setter
    def credentials(self, value):
        self._credentials = value

    @credentials.deleter
    def credentials(self):
        self._credentials = None

    def get_credentials(self):
        """Create user credentials object from service account credentials or an OAuth.

        Try service account credentials first. Fall back to OAuth.
        """
        # service account credentials
        try:
            credentials, project = gauth.load_credentials_from_file(
                self.GOOGLE_APPLICATION_CREDENTIALS
            )
            assert project == self.GOOGLE_CLOUD_PROJECT  # TODO: handle this better

        # OAuth2
        except (TypeError, gauth.exceptions.DefaultCredentialsError) as ekeyfile:
            try:
                credentials = credentials_from_session(self.oauth2)

            except Exception as eoauth:
                raise PermissionError("Cannot obtain credentials.") from Exception(
                    [ekeyfile, eoauth]
                )

        LOGGER.info(
            (
                f"Authenticated to Google Cloud project {self.GOOGLE_CLOUD_PROJECT} with "
                f"credentials {credentials}."
            )
        )

        return credentials

    # OAuth2Session
    @property
    def oauth2(self):
        """OAuth2Session connected to the Google Cloud project."""
        if self._oauth2 is None:
            self._oauth2 = self.authenticate_with_oauth()
        return self._oauth2

    @oauth2.setter
    def oauth2(self, value):
        self._oauth2 = value

    @oauth2.deleter
    def oauth2(self):
        self._oauth2 = None

    def authenticate_with_oauth(self):
        """Guide user through authentication and create `OAuth2Session` for credentials.

        The user will need to visit a URL, authenticate themselves, and authorize
        `PittGoogleConsumer` to make API calls on their behalf.

        The user must have a Google account that is authorized make API calls
        through the project defined by `GOOGLE_CLOUD_PROJECT`.
        Any project can be used, as long as the user has access.

        Additional requirement because this is still in dev: The OAuth is restricted
        to users registered with Pitt-Google, so contact us.
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
        LOGGER.info(
            (
                f"Authenticated to Google Cloud project {self.GOOGLE_CLOUD_PROJECT} with "
                f"OAuth2Session {oauth2}."
            )
        )

        return oauth2
