"""
This does an end-to-end test of the login flow in the entire app.

In particular:

1.  Start with a logged-out user
2.  Check they cannot see logged-in pages
3.  Have them go to ``/authorize`` and pretend they go to Flickr.com
    to complete the log in and approve the app
4.  Simulate them returning to ``/callback`` and being logged in
5.  Check they can now see logged-in pages
6.  Check they can log out again
7.  Check they can no longer see logged-in pages
"""

from flask.testing import FlaskClient
from flask_login import current_user
from vcr.cassette import Cassette


def test_end_to_end(
    flickr_oauth_cassette: Cassette, logged_out_client: FlaskClient
) -> None:
    """
    Do an end-to-end test of our login flow.

    I had to use real OAuth credentials to set up this test.

    What I did:

    1.  Ran the first half of the test, up to the commented-out ``assert 0``.
        This gave me a real authorization URL I could open in Flickr.

    2.  I clicked that authorization URL, which took me to a localhost/…
        URL.  I pasted that into the callback_resp line, and matched the state
        to the session cookie.

    3.  I ran the entire test, with the ``assert 0`` commented out.  This did
        the token exchange with Flickr.

    4.  I redacted the secrets from the URL and the VCR cassette.

    """
    # Rename this variable for clarity -- we will be logged in/out at
    # various points during this test.
    client = logged_out_client

    # Check we aren't currently logged in.
    assert not current_user

    # Check the homepage says we're logged out.
    homepage_resp_1 = client.get("/")
    assert homepage_resp_1.status_code == 200
    assert (
        'You are <strong style="color: red;">logged out</strong>'
        in homepage_resp_1.text
    )

    # Check the user can't access the secret page.
    secret_resp_1 = client.get("/secret")
    assert secret_resp_1.status_code == 302
    assert secret_resp_1.headers["location"] == "/?next=%2Fsecret"

    # Take the user to the login endpoint.  See where we get redirected.
    authorize_resp = client.get("/authorize")

    assert authorize_resp.status_code == 302
    location = authorize_resp.headers["location"]

    # Print that URL -- open this in a browser separately, and make
    # note of where you get redirected.
    print(location)
    # assert 0

    # Now pass the redirect URL in here, as if I had been redirected to
    # the running app.
    callback_url = "http://localhost/callback?oauth_token=72157720941610968-3408ebda02d02c94&oauth_verifier=c80cafc52507f2d4"

    # Now actually visit that URL, and check we complete the login
    # and get passed back to the homepage.
    callback_resp = client.get(callback_url)
    assert callback_resp.status_code == 302
    assert callback_resp.headers["location"] == "/"

    # Check there's now a current user in Flask-Login, which means
    # we're logged in.
    assert current_user

    # Visit the homepage, and check we now see information about
    # the logged-in user.
    homepage_resp_2 = client.get("/")
    assert homepage_resp_2.status_code == 200
    assert (
        'You are <strong style="color: DarkGreen;">logged in</strong>'
        in homepage_resp_2.text
    )
    assert "alexwlchan" in homepage_resp_2.text
    assert "199258389@N04" in homepage_resp_2.text

    # Check we can load the secret page.
    secret_resp_2 = client.get("/secret")
    assert secret_resp_2.status_code == 200

    # Visit the /logout route, and check we become logged out again.
    logout_resp = client.get("/logout")
    assert logout_resp.status_code == 302
    assert logout_resp.headers["location"] == "/"

    # Check the homepage says we're logged out.
    homepage_resp_1 = client.get("/")
    assert homepage_resp_1.status_code == 200
    assert (
        'You are <strong style="color: red;">logged out</strong>'
        in homepage_resp_1.text
    )

    # Check the user can no longer access the secret page.
    secret_resp_3 = client.get("/secret")
    assert secret_resp_3.status_code == 302
    assert secret_resp_3.headers["location"] == "/?next=%2Fsecret"
