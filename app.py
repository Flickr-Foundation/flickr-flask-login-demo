"""
A demo Flask app.
"""

from flask import Flask, render_template


app = Flask(__name__)


@app.route("/")
def homepage() -> str:
    """
    A basic homepage.
    """
    return render_template("homepage.html")
