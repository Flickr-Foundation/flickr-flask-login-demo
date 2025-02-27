"""
A demo app that allows users to log in using Flickr and OAuth.
"""

import sys

from flask import Flask, current_app, redirect, url_for, session, abort, request
from flask_login import (
    UserMixin,
    LoginManager,
    login_user,
    logout_user,
    current_user,
    login_required,
)
from authlib.integrations.httpx_client import OAuth1Client
import json
import keyring
import werkzeug


def create_app() -> Flask:
    """
    Create an instance of the Flask app.
    """
    app = Flask(__name__)

    # Set a secret key for the app.
    #
    # This is used to securely sign the session cookies.  We use a
    # placeholder value here, but you should replace it with a real secret
    # in a real app.
    #
    # See https://flask.palletsprojects.com/en/stable/config/#SECRET_KEY
    app.config["SECRET_KEY"] = "supersecretkey"

    # Get the Flickr API credentials from the system keychain.
    #
    # If either of these are missing, print an error prompting the user
    # to configure their credentials first.
    client_id = keyring.get_password("flickr_flask_login_demo", "key")
    client_secret = keyring.get_password("flickr_flask_login_demo", "secret")

    if client_id is None or client_secret is None:
        sys.exit(
            "You need to save your Flickr API credentials to your keychain before\n"
            "you can run this app:\n"
            "\n"
            "1.  Create a Flickr app at https://www.flickr.com/services/apps/create/\n"
            "2.  Save the credentials to your keychain:\n"
            "\n"
            "    $ keyring set flickr_flask_login_demo key\n"
            "    $ keyring set flickr_flask_login_demo secret\n"
        )

    app.config["CLIENT_ID"] = client_id
    app.config["CLIENT_SECRET"] = client_secret

    # Create a basic login manager using Flask-Login, which will
    # redirect logged-out users to the homepage.
    #
    # See https://blog.miguelgrinberg.com/post/the-flask-mega-tutorial-part-v-user-logins
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = "homepage"
    login_manager.user_loader(load_flickr_user)

    # Create the basic URLs for this app.
    app.add_url_rule("/", view_func=homepage)
    app.add_url_rule("/authorize", view_func=authorize)
    app.add_url_rule("/callback", view_func=callback)
    app.add_url_rule("/logout", view_func=logout)
    app.add_url_rule("/secret", view_func=secret)

    return app


def homepage() -> str:
    """
    A basic homepage.
    """
    if not current_user.is_authenticated:
        return f"""
            <p>This is a Flask app to demonstrate OAuth login using Flickr.</p>
            
            <p>You are <strong style="color: red;">logged out</strong>.</p>
            
            <p>You can <strong><a href="{url_for("authorize")}">log in</a></strong>.</p>
        """
    else:
        return f"""
            <p>This is a Flask app to demonstrate OAuth login using Flickr.</p>
            
            <p>
                You are <strong style="color: DarkGreen;">logged in</strong>
                as <strong>{current_user.name} ({current_user.user_nsid})</strong>.
            </p>
            
            <p>
                You can visit <strong><a href="{url_for("secret")}">the secret page</a></strong> or
                <strong><a href="{url_for("logout")}">log out</a></strong>.
            </p>
        """


def authorize() -> werkzeug.Response:
    """
    Authorize the user.
    """
    if current_user.is_authenticated:
        return redirect(url_for("homepage"))

    # Create an OAuth1Client with the Flickr API key and secret
    client = OAuth1Client(
        client_id=current_app.config["CLIENT_ID"],
        client_secret=current_app.config["CLIENT_SECRET"],
        signature_type="QUERY",
    )

    # Step 1: Getting a Request Token
    #
    # See https://www.flickr.com/services/api/auth.oauth.html#request_token
    #
    # Note: we could put the next_url parameter in here, but this
    # causes issues with the OAuth 1.0a signatures, so I'm passing that
    # in the Flask session instead.
    callback_url = url_for("callback", _external=True)

    request_token_resp = client.fetch_request_token(
        url="https://www.flickr.com/services/oauth/request_token",
        params={"oauth_callback": callback_url},
    )

    request_token = request_token_resp["oauth_token"]

    session["flickr_oauth_request_token"] = json.dumps(request_token_resp)

    # Step 2: Getting the User Authorization
    #
    # This creates an authorization URL on flickr.com, where the user
    # can choose to authorize the app (or not).
    #
    # See https://www.flickr.com/services/api/auth.oauth.html#request_token
    authorization_url = client.create_authorization_url(
        url="https://www.flickr.com/services/oauth/authorize?perms=read",
        request_token=request_token,
    )

    return redirect(authorization_url)


def callback() -> werkzeug.Response:
    """
    Callback from Flickr.
    """
    try:
        request_token = json.loads(session.pop("flickr_oauth_request_token"))
    except (KeyError, ValueError):
        abort(400)

    # Create an OAuth1Client with the Flickr API key and secret, and the request token
    client = OAuth1Client(
        client_id=current_app.config["CLIENT_ID"],
        client_secret=current_app.config["CLIENT_SECRET"],
        token=request_token["oauth_token"],
        token_secret=request_token["oauth_token_secret"],
    )

    # Parse the authorization response from Flickr
    client.parse_authorization_response(request.url)

    # Step 3: Exchanging the Request Token for an Access Token
    #
    # This token gets saved in the OAuth1Client, so we don't need
    # to inspect the response directly.
    #
    # See https://www.flickr.com/services/api/auth.oauth.html#access_token
    token = client.fetch_access_token(
        url="https://www.flickr.com/services/oauth/access_token"
    )

    # The token will be of the form:
    #
    #     {'fullname': 'Flickr User',
    #      'oauth_token': '…',
    #      'oauth_token_secret': '…',
    #      'user_nsid': '123456789@N04',
    #      'username': 'flickruser'}

    # Grab the user stub
    user = FlickrUser(user_nsid=token["user_nsid"], name=token["username"])
    login_user(user)

    return redirect(url_for("homepage"))


def logout() -> werkzeug.Response:
    """
    Logout the user.
    """
    logout_user()
    return redirect(url_for("homepage"))


@login_required
def secret() -> str:
    """
    A secret page.
    """
    return f'This is a secret page. <a href="{url_for("logout")}">Logout</a>'


class FlickrUser(UserMixin):
    """
    A basic user class to satisfy Flask-Login.

    Usually this would be backed by a database or other storage;
    for demo purposes it just stores basic details of the Flickr user.

    See https://flask-login.readthedocs.io/en/latest/#your-user-class
    """

    def __init__(self, user_nsid: str, name: str):
        self.user_nsid = user_nsid
        self.name = name

        # This will store an ID like ``197130754@N07/Flickr Foundation``
        self.id = f"{user_nsid}/{name}"


def load_flickr_user(id: str) -> FlickrUser:
    """
    A basic user loader callback for Flask-Login.

    This doesn't do any checking about whether this user has logged in
    before, or their details, or anything.  You'll need to replace this
    in a real app.

    See https://flask-login.readthedocs.io/en/latest/#how-it-works
    """
    user_nsid, name = id.split("/", 1)
    return FlickrUser(user_nsid, name)
