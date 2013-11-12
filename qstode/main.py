# -*- coding: utf-8 -*-
"""
    qstode.main
    ~~~~~~~~~~~

    Main entry point for the application.

    :copyright: (c) 2012 by Daniel Kertesz
    :license: BSD, see LICENSE for more details.
"""
import os
import logging
import logging.handlers
import argparse
import jinja2
from qstode.app import app, login_manager, oid, whoosh_searcher, db

# import all views
import qstode.views

# import all models
import qstode.model.user
from qstode.model.user import User
import qstode.model.bookmark
from qstode.model.bookmark import Bookmark

# import all Flask-scripts
# import qstode.cli.importer
# import qstode.cli.scuttle_exporter
# import qstode.cli.scuttle_importer
# import qstode.cli.index


def setup_logging(args):
    """Configure logging library for logging through Syslog"""

    level = args.debug and logging.DEBUG or logging.INFO
    syslog_device = app.config.get('SYSLOG_DEVICE', '/dev/log')
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    syslog_handler = logging.handlers.SysLogHandler(address=syslog_device)
    root_logger.addHandler(syslog_handler)

def create_app(cfg=None):
    """Configure the Flask application object and run initialization tasks

    :param cfg: an optional dict containing configuration values
    :returns: an initialized Flask application object
    """

    if cfg is not None:
        app.config.update(cfg)
    app.config.from_envvar('APP_CONFIG', silent=True)

    if 'EXTRA_TEMPLATES' in app.config:
        tpl_loader = jinja2.ChoiceLoader([
            jinja2.FileSystemLoader(app.config['EXTRA_TEMPLATES']),
            app.jinja_loader])
        app.jinja_loader = tpl_loader

    db.init_app(app)
    oid.init_app(app)
    login_manager.init_app(app)
    whoosh_searcher.init_app(app)

    # Register our public access handler, right *AFTER* flask-login
    app.before_request(qstode.views.user.public_access_handler)

    return app

def run_shell(args):
    """Run a python shell

    NOTE: due to python and flask crazyness for all the database query
    you will need to do "use" the flask context with something like:

        with app.app_context():
            print User.query.filter_by(username=u'charlie')
    """

    from qstode.app import db
    from qstode.model.user import User
    from qstode.model.bookmark import Tag, Url, Bookmark

    create_app()
    try:
        import IPython
        IPython.embed()
    except ImportError:
        import code
        shell = code.InteractiveConsole(locals=locals())
        shell.interact()

def run_server(args):
    """Run a local version with werkzeug"""

    create_app().run(host=args.host, port=args.port, debug=args.debug)

def run_setup(args):
    """Initialize QSTode: create DB schema and admin user"""

    _app = create_app()

    with _app.app_context():
        print "Creating DB schema..."
        db.create_all()

        if User.query.filter_by(admin=True).first() is None:
            print "Creating admin user..."
            admin_user = User('admin', 'admin@example.com', 'admin',
                              admin=True)
            db.session.add(admin_user)
            db.session.commit()

def run_wsgi(args):
    """WSGI entry point"""

    application = create_app()
    setup_logging(args)
    return application

def run_reindex(args):
    """Re-index the search engine database"""
    application = create_app()

    with application.app_context():
        writer = whoosh_searcher.get_async_writer()
        for bookmark in Bookmark.query.all():
            whoosh_searcher.add_bookmark(bookmark, writer)
        writer.commit()

def main():
    """Command line entry point"""

    parser = argparse.ArgumentParser(description="QStode utility")
    parser.add_argument('-c', '--config', help="Path to the configuration file")
    subparsers = parser.add_subparsers(help="command help")
    parser.add_argument('-D', '--debug', action='store_true', help="Run in debug mode")

    p_server = subparsers.add_parser('server', help="Run developement server")
    p_server.add_argument('--host', help="Address to bind")
    p_server.add_argument('--port', type=int, help="Port to bind")
    p_server.set_defaults(func=run_server)

    p_setup = subparsers.add_parser('setup', help="Configure QStode")
    p_setup.set_defaults(func=run_setup)

    p_shell = subparsers.add_parser('shell', help="Run a python shell")
    p_shell.set_defaults(func=run_shell)

    p_reindex = subparsers.add_parser(
        'reindex', help="Re-index the search engine database")
    p_reindex.set_defaults(func=run_reindex)

    args = parser.parse_args()

    if not args.config and not 'APP_CONFIG' in os.environ:
        parser.error("You must specify a configuration file")
    else:
        os.environ['APP_CONFIG'] = os.path.abspath(args.config)

    args.func(args)

if __name__ == '__main__':
    main()
