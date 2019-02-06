"""
    qstode.app
    ~~~~~~~~~~

    The base Flask application.

    :copyright: (c) 2012 by Daniel Kertesz
    :license: BSD, see LICENSE for more details.
"""
from functools import wraps
from flask import Flask, request, redirect, g, session
from flask_babel import Babel
from flask_login import LoginManager
from qstode import db


app = Flask("qstode")


# Read the default configuration
app.config.from_object("qstode.default_config")

# initialize extensions
babel = Babel(app)
login_manager = LoginManager()
login_manager.login_view = "login"
login_manager.login_message_category = "warning"


def _guess_lang():
    if "lang" in session:
        return session["lang"]
    else:
        return request.accept_languages.best_match(app.config["SUPPORTED_LANGUAGES_ISO"])


@app.before_request
def autodetect_lang():
    lang = request.args.get("_lang")
    if lang and lang in app.config["SUPPORTED_LANGUAGES_ISO"]:
        session["lang"] = lang
    g.lang = _guess_lang()


@babel.localeselector
def get_locale():
    return g.lang


def ssl_required(fn):
    """Decorator: redirects to the HTTPS version of a route"""

    @wraps(fn)
    def decorated_view(*args, **kwargs):
        if app.config["DEBUG"] or request.is_secure:
            return fn(*args, **kwargs)
        else:
            return redirect(request.url.replace("http://", "https://"))
        return fn(*args, **kwargs)

    return decorated_view


@app.teardown_appcontext
def shutdown_session(response_or_exc):
    db.Session.remove()
    return response_or_exc
