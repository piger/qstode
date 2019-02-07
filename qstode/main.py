"""
    qstode.main
    ~~~~~~~~~~~

    Main entry point for the application.

    :copyright: (c) 2012 by Daniel Kertesz
    :license: BSD, see LICENSE for more details.
"""
import sys
import logging
import click
import jinja2
from flask.logging import default_handler
from .app import app, login_manager
from . import exc, db, utils
from .model import user as user_model

# some circular imports needed to have nice things
from .cli.backup import backup, import_file  # noqa
from .cli.scuttle_importer import import_scuttle  # noqa

from .views import api  # noqa
from .views import admin  # noqa
from .views import bookmark  # noqa
from .views import filters  # noqa
from .views import user  # noqa


# Configure the root logger to pipe everything into the default Flask handler.
rootLogger = logging.getLogger()
rootLogger.addHandler(default_handler)


def create_app(cfg=None):
    """Configure the Flask application object and run initialization tasks

    :param cfg: an optional dict containing configuration values
    :returns: an initialized Flask application object
    """

    if cfg is not None:
        app.config.update(cfg)
    app.config.from_envvar("APP_CONFIG", silent=True)

    if "EXTRA_TEMPLATES" in app.config:
        tpl_loader = jinja2.ChoiceLoader(
            [jinja2.FileSystemLoader(app.config["EXTRA_TEMPLATES"]), app.jinja_loader]
        )
        app.jinja_loader = tpl_loader

    try:
        db.init_db(app.config["SQLALCHEMY_DATABASE_URI"], app)
        login_manager.init_app(app)
    except exc.InitializationError as ex:
        sys.stderr.write("Initialization error: %s\n" % str(ex))
        sys.exit(1)

    # Register our public access handler, right *AFTER* flask-login
    app.before_request(user.public_access_handler)

    return app


@app.cli.command()
def setup():
    """Initialize QSTode: create DB schema and admin user"""

    click.echo("Creating DB schema...")
    db.create_all()

    if user_model.User.query.filter_by(admin=True).first() is None:
        admin_pw = utils.generate_password()
        click.echo("Creating 'admin' user with password '%s'" % admin_pw)
        admin_user = user_model.User("admin", "root@localhost", admin_pw, admin=True)
        db.Session.add(admin_user)
        db.Session.commit()
