# Flickr Flash Auth

This is a boilerplate repo for making a "hello world" page with Flickr Auth.

# Development

You can set up a local development environment by cloning the repo and installing dependencies:

```
$ git clone https://github.com/Flickr-Foundation/flickr-flask-auth.git
$ cd flickr-flask-auth
$ python3 -m venv .venv
$ source .venv/bin/activate
$ pip install -e .
```

You'll need to create a Flickr API key to get a client_id and client_secret, at this URL:

https://www.flickr.com/services/apps/create/

![Screenshot of Flickr API key creation page](flickr-api-screenshot.png)

Once you have those you'll use `keyring` to set them, like so.

```
keyring set flickr_flask_auth key
keyring set flickr_flask_auth secret
```

You can get a local development server with this command:

```
$ python3 -m flask run --debug [--port=nnnn]
```
