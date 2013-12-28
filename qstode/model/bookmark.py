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
import sqlalchemy.types
from sqlalchemy import desc, func, select, and_, not_, or_, cast, distinct
from sqlalchemy import Table, Column, ForeignKey, Integer, String, DateTime
from sqlalchemy import Boolean, event
from sqlalchemy.orm import relationship, backref
from sqlalchemy.ext.associationproxy import association_proxy
from flask_login import current_user
from .. import db
from .user import User, watched_users


bookmark_tags = Table(
    'bookmark_tags', db.Base.metadata,
    Column('bookmark_id', Integer, ForeignKey('bookmarks.id', ondelete='cascade'),
           primary_key=True),
    Column('tag_id', Integer, ForeignKey('tags.id', ondelete='cascade'), primary_key=True))


# http://stackoverflow.com/questions/9234082/setting-delete-orphan-on-sqlalchemy-relationship-causes-assertionerror-this-att
@event.listens_for(db.Session, 'after_flush')
def delete_tag_orphans(session, ctx):
    session.query(Tag).\
        filter(~Tag.bookmarks.any()).\
        delete(synchronize_session=False)


class Tag(db.Base):
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

    __tablename__ = 'tags'

    id = Column(Integer, primary_key=True)
    name = Column(String(35), nullable=False, index=True, unique=True)

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

        related_tags = db.Session.execute(outer_w).fetchall()

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
    def tagcloud(cls, limit=15, min_font_size=2, max_font_size=10,
                 user_id=None):
        """
        Generates a tag cloud.

        Returns a list of dicts with keys:
        - name
        - weight
        - total count
        - (font) size

        for the top `limit` popular Tags.
        """

        query = db.Session.query(Tag, func.count(Tag.id).label('total')).\
                join(Tag.bookmarks).\
                filter(Bookmark.private == False)

        if user_id is not None:
            query = query.join(Bookmark.user).\
                    filter(User.id == user_id)

        query = query.group_by(Tag.id).\
                order_by('total DESC').\
                limit(limit)

        tags = query.all()
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
        query = db.Session.query(cls, count).\
                outerjoin(bookmark_tags).\
                group_by(cls).\
                order_by('total DESC').\
                limit(max_results)

        return query.all()

    def __repr__(self):
        return "<Tag(%r)>" % self.name


class Link(db.Base):
    __tablename__ = 'links'

    id = Column(Integer, primary_key=True)
    href = Column(String(2000), nullable=False)

    def __init__(self, href):
        self.href = href

    @classmethod
    def get_or_create(cls, href):
        result = cls.query.filter_by(href=href).first()
        if result is None:
            return cls(href=href)
        else:
            return result

    def __repr__(self):
        return "<Link(href={})>".format(self.href)


class Bookmark(db.Base):
    """A bookmark element in the archive. It has several properties and
    related tables (URL, Cateory, Tag, etc.).

    db.DateTime columns must store timestamps as if they where from UTC timezone,
    as the `timezone` info is stored only by PostgreSQL database.
    The best practice is to store UTC timestamps and convert to the user
    timezone in the view.
    """

    __tablename__ = 'bookmarks'

    id = Column(Integer, primary_key=True)
    title = Column(String(300), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), index=True)
    link = relationship("Link", lazy='joined', backref=backref('bookmarks'))
    link_id = Column(Integer, ForeignKey('links.id'))
    href = association_proxy('link', 'href')
    private = Column(Boolean, default=False)

    created_on = Column(DateTime, default=datetime.utcnow)
    modified_on = Column(DateTime, default=datetime.utcnow,
                         onupdate=datetime.utcnow)
    indexed_on = Column(DateTime)

    tags = relationship('Tag', secondary=bookmark_tags,
                        backref=backref('bookmarks', lazy='dynamic'),
                        order_by="Tag.name", lazy='subquery')
    notes = Column(String(2500))

    def __init__(self, title, private=False, created_on=None,
                 modified_on=None, notes=None):
        self.title = title
        self.private = private
        if created_on is not None:
            self.created_on = created_on
        if modified_on is not None:
            self.modified_on = modified_on
        self.notes = notes or u""

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
        link = Link.get_or_create(data.get('url'))
        bookmark = Bookmark(title=data.get('title'),
                            private=data.get("private", False),
                            notes=data.get('notes'))
        bookmark.link = link
        bookmark.user = data.get('user')
        for tag in Tag.get_or_create_many(data.get('tags')):
            bookmark.tags.append(tag)
            
        db.Session.add(bookmark)
        db.Session.commit()
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
            order_by(cls.created_on.desc())
        return query

    @classmethod
    def by_user(cls, userid, include_private=False):
        where = (cls.user_id == userid)
        if not include_private:
            where = where & (cls.private == False)
        return cls.query.filter(where).order_by(cls.created_on.desc())

    @classmethod
    def by_followed(cls):
        """Get the latest bookmarks from the users followed by
        the current user"""

        q = cls.query.join(User).\
            outerjoin(watched_users, User.id == watched_users.c.other_user_id).\
            filter(watched_users.c.user_id == current_user.id).\
            filter(cls.private == False).\
            order_by(cls.created_on.desc())

        return q

    @classmethod
    def by_tags(cls, tags, exclude=None):
        """Get bookmark tagged with the specified tags."""

        assert isinstance(tags, list) is True, "`tags` parameter must be " \
            "a list"

        if exclude is None:
            exclude = []

        # enforce lowercase and uniqueness
        tags = set([t.lower() for t in tags])

        if not exclude:
            return cls.get_public().join(cls.tags).\
                filter(Tag.name.in_(tags)).\
                group_by(cls.id).\
                having(func.count(cls.id) == len(tags)).\
                order_by(cls.created_on.desc())

        exclude_query = db.Session.query(bookmark_tags.c.bookmark_id).\
                        join(Tag).\
                        filter(Tag.name.in_(exclude)).\
                        subquery('exclude')

        include_query = db.Session.query(bookmark_tags.c.bookmark_id).\
                        join(Tag).\
                        filter(Tag.name.in_(tags)).\
                        group_by(bookmark_tags.c.bookmark_id).\
                        having(func.count(distinct(Tag.name)) == len(tags)).\
                        subquery('include')

        query = cls.get_public().\
                outerjoin(exclude_query,
                          cls.id == exclude_query.c.bookmark_id).\
                join(include_query,
                     cls.id == include_query.c.bookmark_id).\
                filter(exclude_query.c.bookmark_id == None).\
                order_by(cls.created_on.desc())

        return query

    @classmethod
    def by_ids(cls, ids):
        """Returns a list of Bookmarks matching the IDs in `ids`;
        in MySQL the returned list is ordered the same as `ids`.
        """
        # Keep the order from Whoosh with a MySQL specific hack:
        # order_by FIELD() function.
        # http://dev.mysql.com/doc/refman/5.0/en/string-functions.html#function_field
        engine = db.Session.get_bind()
        if engine.driver.startswith('mysql'):
            query = cls.get_public().filter(cls.id.in_(ids)).\
                    order_by(func.field(cls.id, *ids))
        else:
            query = cls.get_public().filter(cls.id.in_(ids)).\
                    order_by(cls.created_on.desc())
        return query

    @classmethod
    def submit_by_day(cls, days=30):
        date_limit = datetime.now() - timedelta(days)

        # multi-database support (MySQL, PostgreSQL, SQLite) for date conversion
        engine = db.Session.get_bind()
        if engine.driver == 'sqlite':
            fn = cast(func.julianday(cls.created_on), Integer)
        elif engine.driver == 'postgresql':
            fn = cast(cls.created_on, sqlalchemy.types.Date)
        else:
            fn = func.to_days(cls.created_on)

        query = db.Session.query(
            fn.label('day'), func.count('*').label('count')
        ).filter(
            cls.created_on > date_limit
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
            'created_on': self.created_on.isoformat(),
            'modified_on': self.modified_on.isoformat(),
        }

    def __repr__(self):
        return "<Bookmark(title={0}, created_on={1}, private={2}".format(
            self.title, self.created_on, self.private)
