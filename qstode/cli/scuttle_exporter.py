# -*- coding: utf-8 -*-
import sys
import os
import codecs
import re
import json
import calendar
import cgi
from datetime import datetime
from sqlalchemy import *
from sqlalchemy.orm import sessionmaker, relationship, joinedload, mapper
from sqlalchemy.schema import MetaData
from sqlalchemy.engine import reflection
from sqlalchemy.engine.url import make_url
from sqlalchemy.ext.declarative import declarative_base


meta = MetaData()
Session = sessionmaker()

users_table = None
bookmarks_table = None
tags_table = None
watched_table = None


BOOKMARK_FILE_HEADER = \
u"""<!DOCTYPE NETSCAPE-Bookmark-file-1>
<!--This is an automatically generated file.
It will be read and overwritten.
Do Not Edit! -->
<Title>Bookmarks</Title>
<H1>Bookmarks</H1>
<DL><p>
"""

BOOKMARK_FILE_FOOTER_TPL = \
u"""</DL><p><!-- Generated on: {today} -->
"""

BOOKMARK_TPL = \
u"""<DT><A HREF="{href}" ADD_DATE="{add_date}" LAST_MODIFIED="{mod_date}" PRIVATE="{private}" TAGS="{tags}">{title}</A>
"""

class BaseModel(object): pass
class User(BaseModel):
    def to_dict(self):
        return {
            'id': self.uId,
            'username': self.username,
            'password': self.password,
            'created_at': self.uDatetime.isoformat(),
            'modified_at': self.uModified.isoformat(),
            'name': self.name or u'',
            'email': self.email,
            'homepage': self.homepage or u'',
            'content': self.uContent or u'',
            'bookmarks': [],
            'watched_ids': [],
        }

class Bookmark(BaseModel):
    """A Bookmark from Scuttle.

    Notes: the attribute 'status' can have the following values:
    - 0: normal
    - 1: shared
    - 2: private
    """
    def to_dict(self):
        return {
            'id': self.bId,
            'status': self.bStatus,
            'title': self.bTitle or u'',
            'created_at': self.bDatetime.isoformat(),
            'modified_at': self.bModified.isoformat(),
            'url': self.bAddress,
            'description': self.bDescription or u'',
            'hash': self.bHash,
            'tags': [t.tag for t in self.tags],
        }

    @property
    def is_private(self):
        return self.bStatus == 2

class Tag(BaseModel):
    @property
    def name(self):
        return self.tag

class Watched(BaseModel): pass


def read_config(filename):
    """Read and parse a simple 'key = value' configuration file"""
    config = {}

    with open(filename) as fd:
        for n, line in enumerate(fd):
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            try:
                option, value = re.split(r'\s*=\s*', line, 1)
            except ValueError:
                raise SyntaxError("Error in config file at line %d" % n + 1)
            config[option] = value

    return config

def init_db(uri, echo=True):
    """Initialize the database and reflect the tables"""
    global meta

    uri = make_url(uri)
    uri.query.setdefault('charset', 'utf8')

    engine = create_engine(uri, echo=echo)
    meta.bind = engine
    Session.configure(bind=engine)
    reflect_tables()

    return engine

def reflect_tables():
    global users_table, bookmarks_table, tags_table, watched_table

    users_table = Table('sc_users', meta, autoload=True)

    bookmarks_table = Table(
        'sc_bookmarks', meta,
        Column('uId', Integer, ForeignKey('sc_users.uId')),
        autoload=True)

    tags_table = Table(
        'sc_tags', meta,
        Column('bId', Integer, ForeignKey('sc_bookmarks.bId')),
        autoload=True)

    watched_table = Table(
        'sc_watched', meta,
        Column('uId', Integer, ForeignKey('sc_users.uId')),
        Column('watched', Integer, ForeignKey('sc_users.uId')),
        autoload=True)

    mapper(User, users_table, properties={
        'bookmarks': relationship(Bookmark, backref='user'),
        'watched': relationship(
            User, secondary=watched_table,
            lazy='joined',
            primaryjoin=users_table.c.uId==watched_table.c.uId,
            secondaryjoin=users_table.c.uId==watched_table.c.watched)
    })
    mapper(Bookmark, bookmarks_table, properties={
        'tags': relationship(Tag, lazy='joined', backref='bookmark'),
    })
    mapper(Tag, tags_table)
    mapper(Watched, watched_table)

def dt_to_unix(d):
    return calendar.timegm(d.utctimetuple())


def export_scuttle(config_file, outfile='scuttle-export.json'):
    """Export Scuttle data from MySQL to a JSON file"""

    config = read_config(config_file)
    if os.path.exists(outfile):
        print "Output file already exists!"
        sys.exit(1)

    engine = init_db(config['uri'])
    session = Session()
    
    export = {}
    export['users'] = []
    for db_user in session.query(User).\
        options(joinedload('bookmarks'),
                joinedload('watched')):
        user = db_user.to_dict()

        for watched in db_user.watched:
            user['watched_ids'].append(watched.uId)

        export['users'].append(user)

        for bookmark in db_user.bookmarks:
            user['bookmarks'].append(bookmark.to_dict())

    print "Writing output..."

    with codecs.open(outfile, 'w', encoding='utf-8') as fd:
        json.dump(export, fd, ensure_ascii=False, encoding='utf-8')


def export_scuttle_html(config_file, outdir):
    """Export all the bookmarks in a file for each user, using the
    Netscape Bookmark Format"""

    config = read_config(config_file)
    engine = init_db(config['uri'])
    session = Session()

    os.mkdir(outdir)

    for db_user in session.query(User).options(joinedload('bookmarks')):
        if not len(db_user.bookmarks):
            continue
        
        outfile = os.path.join(outdir, db_user.email)
        outfd = codecs.open(outfile, 'w', encoding='utf-8')
        outfd.write(BOOKMARK_FILE_HEADER)

        for bookmark in db_user.bookmarks:
            context = {
                'href': bookmark.bAddress,
                'add_date': dt_to_unix(bookmark.bDatetime),
                'mod_date': dt_to_unix(bookmark.bModified),
                'private': 1 if bookmark.bStatus == 2 else 0,
                'tags': u','.join([t.name for t in bookmark.tags]),
                'title': cgi.escape(bookmark.bTitle),
            }
            data = BOOKMARK_TPL.format(**context)

            outfd.write(data)
            if bookmark.bDescription:
                outfd.write(u"<DD>%s\n" % cgi.escape(bookmark.bDescription))

        outfd.write(BOOKMARK_FILE_FOOTER_TPL.format(
            today=datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
        outfd.close()
        sys.stdout.write('.')
        sys.stdout.flush()

    print

def main():
    from optparse import OptionParser
    parser = OptionParser()
    parser.add_option('-c', '--config')
    (opts, args) = parser.parse_args()
    if not opts.config:
        parser.error("You need to specify a config file")
    export_scuttle(opts.config)
    # export_scuttle_html(opts.config, args[0])

if __name__ == '__main__':
    main()
