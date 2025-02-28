"""
Shared helpers and test fixtures.
"""

from collections.abc import Iterator

from flask import Flask
from flask.testing import FlaskClient
from flask_login import FlaskLoginClient
from nitrate.cassettes import *  # noqa: F403
from nitrate.passwords import use_in_memory_keyring
import os
import pytest
import vcr
from vcr.cassette import Cassette

from app import create_app, FlickrUser


@pytest.fixture
def user() -> FlickrUser:
    """
    Creates a test user who is logged into the app.
    """
    return FlickrUser(user_nsid="test@123", name="Father Sword")


@pytest.fixture
def app() -> Flask:
    """
    Creates a Flask app for testing.
    """
    # Add some placeholder Flickr API credentials to the keychain,
    # so the app can be created correctly.
    client_id = os.environ.get("CLIENT_ID", "123")
    client_secret = os.environ.get("CLIENT_SECRET", "456")

    use_in_memory_keyring(
        initial_passwords={
            ("flickr_flask_login_demo", "key"): client_id,
            ("flickr_flask_login_demo", "secret"): client_secret,
        }
    )

    app = create_app()
    app.config["TESTING"] = True

    return app


@pytest.fixture
def logged_out_client(app: Flask) -> Iterator[FlaskClient]:
    """
    Creates a client for use in testing.

    See https://flask.palletsprojects.com/en/3.0.x/testing/#fixtures
    """
    with app.test_client() as client:
        yield client


@pytest.fixture
def logged_in_client(app: Flask, user: FlickrUser) -> Iterator[FlaskClient]:
    """
    Creates a client for use in testing which is logged in.

    See https://flask-login.readthedocs.io/en/latest/#automated-testing
    """
    app.test_client_class = FlaskLoginClient

    with app.test_client(user=user) as client:
        yield client


@pytest.fixture
def flickr_oauth_cassette(cassette_name: str) -> Iterator[Cassette]:
    """
    Create a vcrpy cassette that records HTTP interactions, so they
    can be replayed later.  This allows you to run the test suite
    without having any OAuth credentials (e.g. in GitHub Actions).

    This cassette will redact any OAuth-related parameters from
    requests and responses.  This ensures that we don't commit
    any real credentials to the test fixtures.
    """
    with vcr.use_cassette(
        cassette_name,
        cassette_library_dir="tests/fixtures/cassettes",
        filter_query_parameters=[
            ("oauth_consumer_key", "OAUTH_CONSUMER_KEY"),
            ("oauth_nonce", "OAUTH_NONCE"),
            ("oauth_signature", "OAUTH_SIGNATURE"),
            ("oauth_timestamp", "OAUTH_TIMESTAMP"),
            ("oauth_verifier", "OAUTH_VERIFIER"),
        ],
        filter_headers=[("authorization", "AUTHORIZATION")],
        decode_compressed_response=True,
    ) as cassette:
        yield cassette
