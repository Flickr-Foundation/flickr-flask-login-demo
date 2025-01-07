"""
A demo Flask app.
"""

from flask import Flask, redirect, url_for, session, abort, request
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

app = Flask(__name__)

# If we're running in production, set a couple of extra config flags
# to ensure we're storing cookies securely -- that is, making them
# only available over HTTPS.
#
# See https://blog.miguelgrinberg.com/post/cookie-security-for-flask-applications
if not app.debug:  # pragma: no cover
    app.config["SESSION_COOKIE_SECURE"] = True
    app.config["REMEMBER_COOKIE_SECURE"] = True

# Set a secret key for the app, this is used to sign the session cookies
app.config["SECRET_KEY"] = "supersecretkey"

# Get the Flickr API key and secret from the keyring, so we can use them to authenticate with Flickr
app.config["CLIENT_ID"] = keyring.get_password("flickr_flask_auth", "key")
app.config["CLIENT_SECRET"] = keyring.get_password("flickr_flask_auth", "secret")

# Initialize the login manager
login = LoginManager()
# Set the login view to the homepage
login.login_view = "homepage"
# Initialize the login manager with the app
login.init_app(app)


class User(UserMixin):
    """
    A simple user class that inherits from Flask-Login's UserMixin.
    """

    def __init__(self, user_id: str):
        """
        Initialize a new User instance.

        Args:
            user_id: The unique identifier for this user
        """
        self.id = user_id


@login.user_loader
def load_user(user_id: str) -> User:
    """
    Basic user loader, read here for more, you will need to implement this (PROPERLY)
    https://flask-login.readthedocs.io/en/latest/#how-it-works
    """

    user = User(user_id)

    # If you want to validate the user, you can do so here
    return user


@app.route("/")
def homepage() -> str:
    """
    A basic homepage.
    """
    if not current_user.is_authenticated:
        return "This is a Flask app to demonstrate OAuth login using Flickr. You are logged out. <a href='/authorize'>Login</a>"

    return (
        f"This is a Flask app to demonstrate OAuth login using Flickr. You are logged in as user {current_user.id}. "
        f"Go view the <a href='/secret'>secret page</a>. <a href='{url_for('logout')}'>Logout</a>"
    )


@app.route("/authorize")
def authorize() -> werkzeug.Response:
    """
    Authorize the user.
    """
    if current_user.is_authenticated:
        return redirect(url_for("homepage"))

    # Create an OAuth1Client with the Flickr API key and secret
    client = OAuth1Client(
        client_id=app.config["CLIENT_ID"],
        client_secret=app.config["CLIENT_SECRET"],
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


@app.route("/callback")
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
        client_id=app.config["CLIENT_ID"],
        client_secret=app.config["CLIENT_SECRET"],
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
    user = load_user(user_id=token["user_nsid"])
    login_user(user)

    return redirect(url_for("homepage"))


@app.route("/logout")
def logout() -> werkzeug.Response:
    """
    Logout the user.
    """
    logout_user()
    return redirect(url_for("homepage"))


@app.route("/secret")
@login_required
def secret() -> str:
    """
    A secret page.
    """
    return f'This is a secret page. <a href="{url_for("logout")}">Logout</a>'
