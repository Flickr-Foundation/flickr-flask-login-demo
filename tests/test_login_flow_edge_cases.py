"""
Tests for edge cases in the login flow, e.g. trying to log in when
you're already logged in.
"""

import typing

from flask.testing import FlaskClient
import pytest


@pytest.mark.parametrize("url", ["/authorize", "/callback"])
def test_login_when_logged_in(logged_in_client: FlaskClient, url: str) -> None:
    """
    If you're logged in and you try to go back through the login flow,
    you're immediately redirected to the homepage.
    """
    resp = logged_in_client.get(url)
    assert resp.status_code == 302
    assert resp.headers["location"] == "/"


def test_logout_when_logged_out(logged_out_client: FlaskClient) -> None:
    """
    If you're logged in and you try to log out again, you're redirected
    to the homepage.
    """
    resp = logged_out_client.get("/logout")
    assert resp.status_code == 302
    assert resp.headers["location"] == "/"


def test_callback_without_request_token_is_error(
    logged_out_client: FlaskClient,
) -> None:
    """
    If you try to go through the callback flow without a request token
    in your session, the login fails.
    """
    resp = logged_out_client.get("/callback")
    assert resp.status_code == 400


@pytest.mark.parametrize(
    "request_token",
    [None, "hello world", {}, {"oauth_token": "123"}, {"oauth_token_secret": "456"}],
)
def test_callback_with_malformed_request_token_is_error(
    logged_out_client: FlaskClient, request_token: typing.Any
) -> None:
    """
    If you try to go through the callback flow and the request token
    exists but it's the wrong format, the login fails.
    """
    with logged_out_client.session_transaction() as session:
        session["request_token"] = request_token

    resp = logged_out_client.get("/callback")
    assert resp.status_code == 400


@pytest.mark.parametrize(
    "url", ["/callback", "/callback?oauth_token=123", "/callback?oauth_verifier=456"]
)
def test_callback_without_query_params_is_error(
    logged_out_client: FlaskClient, url: str
) -> None:
    """
    If you try to go through the callback flow with incorrect query parameters
    in the URL, the login fails.
    """
    resp = logged_out_client.get(url)
    assert resp.status_code == 400
