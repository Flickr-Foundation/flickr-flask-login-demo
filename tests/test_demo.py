"""
Tests related to the demo specifically, which are unlikely to
be important to other Flask apps.
"""

from nitrate.passwords import use_in_memory_keyring
import pytest

from app import create_app


def test_no_client_id_is_error() -> None:
    """
    If you try to start the demo app without a client ID, it fails and
    gives you a helpful error message explaining you need to configure
    the Flickr API first.
    """
    use_in_memory_keyring(initial_passwords={})

    with pytest.raises(
        SystemExit, match="You need to save your Flickr API credentials"
    ):
        create_app()


def test_no_client_secret_is_error() -> None:
    """
    If you try to start the demo app without a client secret, it fails and
    gives you a helpful error message explaining you need to configure
    the Flickr API first.
    """
    use_in_memory_keyring(initial_passwords={("flickr_flask_login_demo", "key"): "123"})

    with pytest.raises(
        SystemExit, match="You need to save your Flickr API credentials"
    ):
        create_app()
