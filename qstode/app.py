# -*- coding: utf-8 -*-
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
from . import searcher
from . import db

app = Flask('qstode')

# Set some configuration defaults
app.config['USER_REGISTRATION_ENABLED'] = True

app.config['SUPPORTED_LANGUAGES'] = [
    ('en', 'English'),
    ('it', 'Italiano'),
]
app.config['SUPPORTED_LANGUAGES_ISO'] = [
    l[0] for l in app.config['SUPPORTED_LANGUAGES']]

# Number of Bookmarks returned on every page
app.config['PER_PAGE'] = 10

# Number of Bookmarks returned in the RSS feed
app.config['FEED_NUM_ENTRIES'] = 15


babel = Babel(app)
login_manager = LoginManager()
login_manager.login_view = "login"
login_manager.login_message_category = "warning"
whoosh_searcher = searcher.WhooshSearcher()


def _guess_lang():
    if "lang" in session:
        return session["lang"]
    else:
        return request.accept_languages.best_match(
            app.config["SUPPORTED_LANGUAGES_ISO"])

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
        if app.config['DEBUG'] or request.is_secure:
            return fn(*args, **kwargs)
        else:
            return redirect(request.url.replace("http://", "https://"))
        return fn(*args, **kwargs)
    return decorated_view

@app.teardown_appcontext
def shutdown_session(exception=None):
    db.Session.remove()
