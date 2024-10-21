"""
Shared helpers and test fixtures.
"""

from collections.abc import Iterator

from flask.testing import FlaskClient
import pytest


@pytest.fixture()
def client() -> Iterator[FlaskClient]:
    """
    Creates a client for use in testing.

    See https://flask.palletsprojects.com/en/3.0.x/testing/#fixtures
    """
    from app import app

    with app.test_client() as client:
        yield client
