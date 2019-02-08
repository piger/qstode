"""
    qstode.app
    ~~~~~~~~~~

    The base Flask application.

    :copyright: (c) 2012 by Daniel Kertesz
    :license: BSD, see LICENSE for more details.
"""
import os
from functools import wraps
from flask import Flask, request, redirect, g, session, send_from_directory, render_template
from flask_babel import Babel
from flask_login import LoginManager
from . import db


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


# robots.txt
@app.route("/robots.txt")
def robotstxt():
    return send_from_directory(
        os.path.join(app.root_path, "static"), "robots.txt", mimetype="text/plain"
    )


@app.errorhandler(404)
def page_not_found(error):
    return render_template("404.html"), 404


@app.errorhandler(500)
def internal_error(error):
    db.Session.rollback()
    return render_template("500.html"), 500


@app.errorhandler(403)
def permission_denied(e):
    """Handle the 403 error code for permission protected pages"""
    return render_template("permission_denied.html"), 403


@app.route("/help")
def help():
    return render_template("help.html")
