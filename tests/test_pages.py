"""
Tests for the two pages in the app, the homepage and the secret page.

We want to test whether they're visible to logged in/logged out users,
and that they display the right information.

In a larger app with more complex pages, we might break these into
separate test files, e.g. one file per route.
"""

from flask.testing import FlaskClient
from app import FlickrUser


def test_homepage_when_logged_out(logged_out_client: FlaskClient) -> None:
    """
    The homepage says "Logged out" when the user is not logged in.
    """
    resp = logged_out_client.get("/")
    assert resp.status_code == 200

    # It has the correct message
    assert "logged out" in resp.text

    # It has a link to login
    assert '<a href="/authorize">log in</a>' in resp.text


def test_homepage_when_logged_in(
    logged_in_client: FlaskClient, user: FlickrUser
) -> None:
    """
    The homepage says "Logged in" when the user is logged in.
    """
    resp = logged_in_client.get("/")
    assert resp.status_code == 200

    # It has the correct message
    assert "logged in" in resp.text

    # It has a link to logout
    assert '<a href="/logout">log out</a>' in resp.text

    # It has a link to the secret page
    assert '<a href="/secret">secret page</a>' in resp.text

    # It displays the user's id
    assert user.user_nsid in resp.text


def test_secret_page_when_logged_out(logged_out_client: FlaskClient) -> None:
    """
    The secret page is not viewable when the user is logged out.
    """
    resp = logged_out_client.get("/secret")
    assert resp.status_code == 302


def test_secret_page_when_logged_in(logged_in_client: FlaskClient) -> None:
    """
    The secret page is viewable when the user is logged in.
    """
    resp = logged_in_client.get("/secret")
    assert resp.status_code == 200

    # It has the correct message
    assert "<strong>secret page</strong>" in resp.text
