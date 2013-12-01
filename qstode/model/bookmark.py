# -*- coding: utf-8 -*-
"""
    qstode.model.bookmark
    ~~~~~~~~~~~~~~~~~~~~~

    SQLAlchemy model definitions for bookmark related objects.

    :copyright: (c) 2012 by Daniel Kertesz
    :license: BSD, see LICENSE for more details.
"""
import math
from datetime import datetime, timedelta
from sqlalchemy import (desc, func, select, and_,
                        not_, or_, cast, distinct)
import sqlalchemy.types
from sqlalchemy.ext.associationproxy import association_proxy
from flask_login import current_user
from qstode.app import db


bookmark_tags = db.Table(
    'bookmark_tags',
    db.Column('bookmark_id', db.Integer, db.ForeignKey('bookmark.id'),
           primary_key=True),
    db.Column('tag_id', db.Integer, db.ForeignKey('tag.id'),
           primary_key=True),
)

class Tag(db.Model):
    """This seemingly harmless class describes the `Tag` model that is the
    most important piece of this application; tag names are stored treated
    always lowercase because otherwise it would be a mess.

    An important consideration must be done regarding MySQL and the
    collation: with the default collation for utf8 (utf8_general_ci)
    names like "perù" and "peru" are considered to be equals; to have
    a literal comparison we should use the collation 'utf8_bin', but
    there is a problem with `MySQL-Python` 1.2.3 (the default shipped
    with Debian 7) where 'utf8_bin' columns will always emit 'str' strings, even
    specifying `convert_unicode=True` in the sql engine configuration.
    Setting the column type to `Unicode` with collation `utf8_bin` doesn't solve
    the problem. The only solution is to upgrade to MySQL-Python 1.2.4
    or to specify a generic collation.

    See also: http://sourceforge.net/p/mysql-python/bugs/289/
    """
    # Uncomment this line to enable the "right" collation for tag names.
    # __table_args__ = {'mysql_collate': 'utf8_bin'}

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(35), nullable=False, index=True, unique=True)

    def __init__(self, name):
        """Create a new Tag, enforcing a lowercase name"""
        self.name = name.lower()

    @classmethod
    def get_or_create(cls, name):
        result = cls.query.filter_by(name=name).first()
        if result is None:
            return cls(name)
        else:
            return result

    @classmethod
    def search(cls, term):
        query = cls.query.filter(cls.name.startswith(term)).\
                order_by(cls.name.asc())
        return query

    @staticmethod
    def get_related(tags, limit=20):
        """
        Returns a list of tuples (Tag.id, Tag.name, count) for each Tag related
        to `tags`.

        Source: http://pieceofpy.com/category/sqlalchemy/2/

        WARNING: This is currently broken on MySQL; the query must be redesigned
        and rewritten.
        """

        # XXX
        # This MUST be optimized -- smashes MySQL! :(
        return []

        tags = [t.lower() for t in tags]
        tag_count = len(tags)

        inner_q = select([bookmark_tags.c.bookmark_id])
        inner_w = inner_q.where(
            and_(bookmark_tags.c.tag_id == Tag.id, Tag.name.in_(tags))
        ).group_by(
            bookmark_tags.c.bookmark_id
        ).having(
            func.count(bookmark_tags.c.bookmark_id) == tag_count
        ).correlate(None)

        outer_q = select([Tag.id, Tag.name,
                          func.count(
                              bookmark_tags.c.bookmark_id
                          ).label('tot')])
        outer_w = outer_q.where(
            and_(
                bookmark_tags.c.bookmark_id.in_(inner_w),
                not_(Tag.name.in_(tags)),
                Tag.id == bookmark_tags.c.tag_id
            )
        ).group_by(bookmark_tags.c.tag_id).\
                order_by(desc('tot')).limit(limit)

        related_tags = db.session.execute(outer_w).fetchall()

        return related_tags

    @classmethod
    def get_or_create_many(cls, names):
        """
        Returns a list of Tag objects matching `names` and create Tags
        that can't be found.
        """
        results = []
        names = set([n.lower() for n in names])

        for name in names:
            tag = cls.query.filter_by(name=name).first()
            if tag is None:
                tag = cls(name)
            results.append(tag)

        return results

    @classmethod
    def get_many(cls, names):
        """
        Returns a list of Tags matching `names`.
        """
        results = []
        names = [n.lower() for n in names]

        for name in names:
            tag = cls.query.filter_by(name=name).first()
            if tag is not None:
                results.append(tag)
        return results

    @classmethod
    def tagcloud(cls, limit=15, min_font_size=2, max_font_size=10):
        """
        Generates a tag cloud.

        Returns a list of dicts with keys:
        - name
        - weight
        - total count
        - (font) size

        for the top `limit` popular Tags.
        """

        tags = db.session.query(Tag, func.count(Tag.id).label('total')).\
                join('bookmarks').\
                filter(Bookmark.private == False).\
                group_by(Tag.id).\
                order_by('total DESC').\
                limit(limit)

        if len(tags) < limit:
            return []

        # The total count of the most popular tag
        tot_max = tags[0][1]
        # The total count of the least popular tag
        tot_min = tags[-1][1]

        tag_cloud_weighted = []
        for tag, tag_count in tags:
            weight = ( math.log(tag_count) - math.log(tot_min) ) / ( math.log(tot_max) - math.log(tot_min) )
            tag_dict = {
                'name': tag.name,
                'weight': weight,
                'tot': tag_count,
                'size': int(min_font_size + round((max_font_size - min_font_size) * weight),)
            }
            tag_cloud_weighted.append(tag_dict)

        tag_cloud_weighted = sorted(tag_cloud_weighted, key=lambda x:x['name'],
                                    reverse=False)

        return tag_cloud_weighted

    @classmethod
    def taglist(cls, max_results=20):
        """
        Returns a list of tuples (Tag object, total count) for the most popular
        tags.
        """

        count = func.count(bookmark_tags.c.bookmark_id).label('total')
        query = db.session.query(cls, count).\
                outerjoin(bookmark_tags).\
                group_by(cls).\
                order_by('total DESC').\
                limit(max_results)

        return query.all()

    def __repr__(self):
        return "<Tag(%r)>" % self.name


class Url(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String(2000), nullable=False)

    @classmethod
    def get_or_create(cls, url):
        result = cls.query.filter_by(url=url).first()
        if result is None:
            return cls(url)
        else:
            return result

    def __init__(self, url):
        self.url = url

    def __repr__(self):
        return '<URL(%r)>' % self.url


class Bookmark(db.Model):
    """A bookmark element in the archive. It has several properties and
    related tables (URL, Cateory, Tag, etc.).

    db.DateTime columns must store timestamps as if they where from UTC timezone,
    as the `timezone` info is stored only by PostgreSQL database.
    The best practice is to store UTC timestamps and convert to the user
    timezone in the view.
    """

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(300), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), index=True)
    url = db.relationship("Url", lazy='joined', backref=db.backref('bookmarks'))
    url_id = db.Column(db.Integer, db.ForeignKey('url.id'))
    href = association_proxy('url', 'url')
    private = db.Column(db.Boolean, default=False)

    creation_date = db.Column(db.DateTime(), default=datetime.utcnow)
    last_modified = db.Column(db.DateTime(), default=datetime.utcnow,
                           onupdate=datetime.utcnow)

    tags = db.relationship('Tag', secondary=bookmark_tags,
                           backref=db.backref('bookmarks', lazy='dynamic'),
                           order_by="Tag.name", lazy='subquery')
    notes = db.Column(db.String(2500))

    def __init__(self, title, url, private=False, creation_date=None,
                 last_modified=None, notes=u'',
                 user=None, tags=None):
        self.title = title
        self.url = url
        self.private = private
        if creation_date is not None:
            self.creation_date = creation_date
        else:
            self.creation_date = datetime.utcnow()
        if last_modified is not None:
            self.last_modified = last_modified
        else:
            self.last_modified = self.creation_date
        self.notes = notes
        if user is not None:
            self.user = user
        if tags is not None:
            self.tags.extend(tags)

    @classmethod
    def create(cls, data):
        """Helper for creating new Bookmark objects.

        :param data: a dict containing the following items:

        - url: the bookmark URL (e.g. http://www.example.com/)
        - title: a unicode string with the bookmark title
        - notes: a unicode string with the bookmark notes
        - tags: a list of unicode strings with the bookmark tags
        - user: a `model.User` object with the owner of the bookmark
        - private: an optional boolean value to make the bookmark private

        :returns: the bookmark just created
        """
        url = Url.get_or_create(data.get('url'))

        bookmark = Bookmark(title=data.get('title'),
                            url=url,
                            private=data.get("private", False),
                            creation_date=datetime.utcnow(),
                            notes=data.get('notes'))
                     
        bookmark.user = data.get('user')
        for tag in Tag.get_or_create_many(data.get('tags')):
            bookmark.tags.append(tag)
            
        db.session.add(bookmark)
        db.session.commit()
        return bookmark

    @classmethod
    def get_public(cls):
        """Return a query for the list of latest public Bookmarks, including
        the private bookmarks for the current user"""

        if current_user.is_authenticated():
            return cls.query.filter(or_(
                and_(cls.private == True, cls.user_id == current_user.id),
                cls.private == False))
        else:
            return cls.query.filter(cls.private == False)
        
    @classmethod
    def get_latest(cls):
        query = cls.get_public().\
            order_by(cls.creation_date.desc())
        return query

    @classmethod
    def by_user(cls, userid, include_private=False):
        where = (cls.user_id == userid)
        if not include_private:
            where = where & (cls.private == False)
        return cls.query.filter(where).order_by(cls.creation_date.desc())

    @classmethod
    def by_tags(cls, tags, exclude=None):
        if exclude is None:
            exclude = []

        # enforce lowercase and uniqueness
        tags = set([t.lower() for t in tags])

        if not exclude:
            return cls.get_public().join(cls.tags).\
                filter(Tag.name.in_(tags)).\
                group_by(cls.id).\
                having(func.count(cls.id) == len(tags)).\
                order_by(cls.creation_date.desc())

        exclude_query = db.session.query(bookmark_tags.c.bookmark_id).\
                        join(Tag).\
                        filter(Tag.name.in_(exclude)).\
                        subquery('exclude')

        include_query = db.session.query(bookmark_tags.c.bookmark_id).\
                        join(Tag).\
                        filter(Tag.name.in_(tags)).\
                        group_by(bookmark_tags.c.bookmark_id).\
                        having(func.count(distinct(Tag.name)) == len(tags)).\
                        subquery('include')

        query = cls.get_public().\
                outerjoin(exclude_query,
                          Bookmark.id == exclude_query.c.bookmark_id).\
                join(include_query,
                     Bookmark.id == include_query.c.bookmark_id).\
                filter(exclude_query.c.bookmark_id == None).\
                order_by(cls.creation_date.desc())

        return query

    @classmethod
    def by_ids(cls, ids):
        """Returns a list of Bookmarks matching the IDs in `ids`;
        in MySQL the returned list is ordered the same as `ids`.
        """
        # Keep the order from Whoosh with a MySQL specific hack:
        # order_by FIELD() function.
        # http://dev.mysql.com/doc/refman/5.0/en/string-functions.html#function_field
        if db.engine.driver.startswith('mysql'):
            query = cls.get_public().filter(cls.id.in_(ids)).\
                    order_by(func.field(cls.id, *ids))
        else:
            query = cls.get_public().filter(cls.id.in_(ids)).\
                    order_by(cls.creation_date.desc())
        return query

    @classmethod
    def submit_by_day(cls, days=30):
        date_limit = datetime.now() - timedelta(days)

        # multi-database support (MySQL, PostgreSQL, SQLite) for date conversion
        driver = db.engine.driver
        if driver == 'sqlite':
            fn = cast(func.julianday(cls.creation_date), db.Integer)
        elif driver == 'postgresql':
            fn = cast(cls.creation_date, sqlalchemy.types.Date)
        else:
            fn = func.to_days(cls.creation_date)

        query = db.session.query(
            fn.label('day'), func.count('*').label('count')
        ).filter(
            cls.creation_date > date_limit
        ).group_by('day').order_by('day ASC')

        results = [row.count for row in query.all()]
        return results

    def to_dict(self):
        return {
            'id': self.id,
            'url': self.href,
            'title': self.title,
            'notes': self.notes,
            'tags': [tag.name for tag in self.tags],
            'private': self.private,
            'creation_date': self.creation_date.isoformat(),
            'last_modified': self.last_modified.isoformat(),
        }

    def __repr__(self):
        return '<Bookmark(title=%r, url=%r)>' % (self.title, self.url)
