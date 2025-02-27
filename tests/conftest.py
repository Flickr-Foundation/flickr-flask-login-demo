"""
Shared helpers and test fixtures.
"""

from collections.abc import Iterator

from flask.testing import FlaskClient
import pytest
import secrets

from flask_login import FlaskLoginClient
from app import User


@pytest.fixture
def user() -> User:
    """
    Creates a test user who is logged into the app.
    """
    random_string = secrets.token_hex()

    user = User(id=f"test@{random_string}")

    return user


@pytest.fixture()
def logged_out_client() -> Iterator[FlaskClient]:
    """
    Creates a client for use in testing.

    See https://flask.palletsprojects.com/en/3.0.x/testing/#fixtures
    """
    from app import app

    with app.test_client() as client:
        yield client


@pytest.fixture
def logged_in_client(user: User) -> Iterator[FlaskClient]:
    """
    Creates a client for use in testing which is logged in.

    See https://flask-login.readthedocs.io/en/latest/#automated-testing
    """
    from app import app

    app.test_client_class = FlaskLoginClient
    with app.test_client(user=user) as client:
        yield client
