"""
Shared helpers and test fixtures.
"""

from collections.abc import Iterator

from flask import Flask
from flask.testing import FlaskClient
from flask_login import FlaskLoginClient
from nitrate.passwords import use_in_memory_keyring
import pytest

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
    use_in_memory_keyring(
        initial_passwords={
            ("flickr_flask_login_demo", "key"): "123",
            ("flickr_flask_login_demo", "secret"): "456",
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
