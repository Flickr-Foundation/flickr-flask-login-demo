"""
A demo Flask app.
"""
from flask import Flask, redirect, url_for, session
from flask_login import LoginManager, current_user, UserMixin, login_required
from authlib.integrations.httpx_client import OAuth1Client
import json
import keyring

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
    def __init__(self, user_id):
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
    return User(user_id)


@app.route("/")
def homepage() -> str:
    """
    A basic homepage.
    """
    if not current_user.is_authenticated:
        return "This is a Flask app to demonstrate OAuth login using Flickr. You are logged out. <a href='/authorize'>Login</a>"
    
    return f"This is a Flask app to demonstrate OAuth login using Flickr. You are logged in as user {current_user.id}."

@app.route("/authorize")
def authorize():
    """
    Authorize the user.
    """
    if current_user.is_authenticated:
        return redirect(url_for("homepage"))

    client = OAuth1Client(
        client_id=app.config["CLIENT_ID"],
        client_secret=app.config["CLIENT_SECRET"],
        signature_type="QUERY"
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
def callback():
    """
    Callback from Flickr.
    """
    return "This is a callback from Flickr."

@app.route("/secret")
@login_required
def secret():
    """
    A secret page.
    """
    return "This is a secret page."
