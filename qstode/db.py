# -*- coding: utf-8 -*-
"""
    qstode.db
    ~~~~~~~~~

    SQLAlchemy initialization and base configuration classes; most of the
    code is taken from Flask-SQLAlchemy by Armin Ronacher:
    https://github.com/mitsuhiko/flask-sqlalchemy

    :copyright: (c) 2013 by Daniel Kertesz
    :license: BSD, see LICENSE for more details.
"""
from flask import abort
from sqlalchemy import create_engine
from sqlalchemy import orm
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.engine.url import make_url
from . import utils


class BaseQuery(orm.Query):
    """The default query object used for models, and exposed as
    :attr:`~SQLAlchemy.Query`. This can be subclassed and
    replaced for individual models by setting the :attr:`~Model.query_class`
    attribute.  This is a subclass of a standard SQLAlchemy
    :class:`~sqlalchemy.orm.query.Query` class and has all the methods of a
    standard query as well.
    """

    def get_or_404(self, ident):
        """Like :meth:`get` but aborts with 404 if not found instead of
        returning `None`.
        """
        rv = self.get(ident)
        if rv is None:
            abort(404)
        return rv

    def first_or_404(self):
        """Like :meth:`first` but aborts with 404 if not found instead of
        returning `None`.
        """
        rv = self.first()
        if rv is None:
            abort(404)
        return rv

    def paginate(self, page, per_page=20, error_out=True):
        """Returns `per_page` items from page `page`.  By default it will
        abort with 404 if no items were found and the page was larger than
        1.  This behavor can be disabled by setting `error_out` to `False`.

        Returns an :class:`Pagination` object.
        """
        if error_out and page < 1:
            abort(404)
        items = self.limit(per_page).offset((page - 1) * per_page).all()
        if not items and page != 1 and error_out:
            abort(404)

        # No need to count if we're on the first page and there are fewer
        # items than we expected.
        if page == 1 and len(items) < per_page:
            total = len(items)
        else:
            total = self.order_by(None).count()

        return utils.Pagination(self, page, per_page, total, items)


Session = orm.scoped_session(orm.sessionmaker(autocommit=False, autoflush=False,
                                              query_cls=BaseQuery))
Base = declarative_base()
Base.query = Session.query_property()


def init_alembic(config_file="alembic.ini"):
    """Initialize alembic (i.e. set the migration version to "current")
    for a fresh database."""

    from alembic.config import Config
    from alembic import command
    
    alembic_cfg = Config(config_file)
    command.stamp(alembic_cfg, "head")


def init_db(uri, app=None, create=False):
    # we must import all SQLAlchemy models here
    from . import model

    options = { 'convert_unicode': True }

    if app is not None and app.config.get('DEBUG'):
        options['echo'] = True

    info = make_url(uri)
    if info.drivername.startswith('mysql'):
        info.query.setdefault("charset", "utf8")
        options.setdefault("pool_size", 10)
        options.setdefault("pool_recycle", 7200)
    elif info.drivername == 'sqlite':
        if info.database not in (None, '', ':memory:'):
            from sqlalchemy.pool import NullPool
            options['poolclass'] = NullPool

    engine = create_engine(info, **options)
    Session.configure(bind=engine)
    if create is True:
        create_all(engine)

    return engine

def create_all(engine=None, enable_alembic=False):
    if engine is None:
        engine = Session.get_bind()
    Base.metadata.create_all(engine)
    if enable_alembic:
        init_alembic()


def drop_all(engine=None):
    engine = engine or Session.get_bind()
    Base.metadata.drop_all(engine)
