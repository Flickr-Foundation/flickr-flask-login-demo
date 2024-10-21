"""Tests for the homepage, i.e. /"""

from flask.testing import FlaskClient


def test_can_load_homepage(client: FlaskClient) -> None:
    """
    You can load the homepage.
    """
    resp = client.get("/")
    assert resp.status_code == 200
    assert b"This is a Flask app" in resp.data
