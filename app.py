"""
A demo app that allows users to log in using Flickr and OAuth.
"""

import sys

from authlib.integrations.httpx_client import OAuth1Client
from flask import Flask, current_app, redirect, url_for, session, abort, request
from flask_login import (
    UserMixin,
    LoginManager,
    login_user,
    logout_user,
    current_user,
    login_required,
)
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

    # Set the permissions that the app needs from Flickr -- read, write
    # or delete.
    app.config["FLICKR_PERMISSIONS"] = "read"

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
                You can visit the <strong><a href="{url_for("secret")}">secret page</a></strong> or
                <strong><a href="{url_for("logout")}">log out</a></strong>.
            </p>
        """


def authorize() -> werkzeug.Response:
    """
    This is the first step of logging in with Flickr.

    We get a request token from Flickr, and then we redirect the user
    to Flickr.com where they can log in and approve our app.
    """
    # If the user is already logged in, we don't need to send them
    # through the authentication flow here -- we can redirect them
    # straight to the homepage.
    if current_user.is_authenticated:
        return redirect(url_for("homepage"))

    # Create an OAuth1Client with the Flickr API key and secret
    oauth_client = OAuth1Client(
        client_id=current_app.config["CLIENT_ID"],
        client_secret=current_app.config["CLIENT_SECRET"],
        signature_type="QUERY",
    )

    # Where will the user be redirected after they approve our app
    # on Flickr.com?
    #
    # We use ``_external=True`` because we want an absolute URL rather
    # than a relative URL.  It's the difference between ``/callback``
    # and ``https://example.com/callback``.
    callback_url = url_for("callback", _external=True)

    # Step 1: Get a Request Token
    #
    # This will return an OAuth token and secret, in the form:
    #
    #     {'oauth_callback_confirmed': 'true',
    #      'oauth_token': '721…b37',
    #      'oauth_token_secret': '7e2…91a'}
    #
    # See https://www.flickr.com/services/api/auth.oauth.html#request_token
    request_token = oauth_client.fetch_request_token(
        url="https://www.flickr.com/services/oauth/request_token",
        params={"oauth_callback": callback_url},
    )

    # Save the request token in the user session -- we'll need it in
    # the Flickr callback when we exchange the request token for
    # an access token.
    session["request_token"] = request_token

    # Step 2: Getting the User Authorization
    #
    # This creates an authorization URL on flickr.com, where the user
    # can choose to authorize the app (or not).
    #
    # See https://www.flickr.com/services/api/auth.oauth.html#request_token
    authorization_url = oauth_client.create_authorization_url(
        url=f"https://www.flickr.com/services/oauth/authorize?perms={current_app.config['FLICKR_PERMISSIONS']}"
    )

    # Redirect the user to the Flickr.com URL where they can log in
    # and approve our app.
    return redirect(authorization_url)


def callback() -> werkzeug.Response:
    """
    Handle the authorization callback from Flickr.

    After a user approves our app on Flickr.com, they'll be redirected
    back to our app at this URL with some extra parameters, e.g.

        /callback?oauth_token=721…3fd&oauth_verifier=79f…883

    We can use these tokens to get an access token for the user which
    can make Flickr API requests on their behalf.
    """
    # Get the request token from the Flask session, which we saved in
    # the /authorize step.
    #
    # If we can't retrieve this token for some reason, we can't complete
    # the login process, so we need to bail out.
    try:
        request_token = session.pop("request_token")

        oauth_token = request_token["oauth_token"]
        oauth_token_secret = request_token["oauth_token_secret"]
    except (KeyError, ValueError):
        abort(400)

    # Create an OAuth1Client with the Flickr API key and secret.
    #
    # We need to include the request token that we received in the
    # previous step.
    oauth_client = OAuth1Client(
        client_id=current_app.config["CLIENT_ID"],
        client_secret=current_app.config["CLIENT_SECRET"],
        token=oauth_token,
        token_secret=oauth_token_secret,
    )

    # Parse the authorization response from Flickr -- that is, extract
    # the OAuth query parameters from the URL, and add them to the client.
    oauth_client.parse_authorization_response(request.url)

    # Step 3: Exchanging the Request Token for an Access Token
    #
    # The access token we receive will be of the form:
    #
    #     {'fullname': 'Flickr User',
    #      'oauth_token': '…',
    #      'oauth_token_secret': '…',
    #      'user_nsid': '123456789@N04',
    #      'username': 'flickruser'}
    #
    # See https://www.flickr.com/services/api/auth.oauth.html#access_token
    access_token = oauth_client.fetch_access_token(
        url="https://www.flickr.com/services/oauth/access_token"
    )

    # Create a stub user, and log them in with Flask-Login.  Then we
    # redirect to the homepage, where it will recognise them as
    # being logged in.
    user = FlickrUser(
        user_nsid=access_token["user_nsid"], name=access_token["username"]
    )
    login_user(user)

    return redirect(url_for("homepage"))


def logout() -> werkzeug.Response:
    """
    Log out the user.
    """
    logout_user()
    return redirect(url_for("homepage"))


@login_required
def secret() -> str:
    """
    A secret page, which is only accessible to logged-in users.
    """
    return f"""
        <p>
            This is a <strong>secret page</strong> which is only visible to logged-in users.
        </p>
        <p>
            You can <strong><a href="{url_for("homepage")}">return to the homepage</a></strong> 
            or <strong><a href="{url_for("logout")}">log out</a></strong>.
        </p>
    """


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
