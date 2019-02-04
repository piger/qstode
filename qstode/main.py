"""
    qstode.main
    ~~~~~~~~~~~

    Main entry point for the application.

    :copyright: (c) 2012 by Daniel Kertesz
    :license: BSD, see LICENSE for more details.
"""
import sys
import click
import jinja2
from qstode.app import app, login_manager
from qstode import exc
from qstode import db
from qstode import utils

# some circular imports needed to have nice things
from qstode import views  # noqa
from qstode import model  # noqa
from qstode import cli  # noqa


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
    app.before_request(views.user.public_access_handler)

    return app


@app.cli.command()
def setup():
    """Initialize QSTode: create DB schema and admin user"""

    click.echo("Creating DB schema...")
    db.create_all()

    if model.User.query.filter_by(admin=True).first() is None:
        admin_pw = utils.generate_password()
        click.echo("Creating 'admin' user with password '%s'" % admin_pw)
        admin_user = model.User("admin", "root@localhost", admin_pw, admin=True)
        db.Session.add(admin_user)
        db.Session.commit()
