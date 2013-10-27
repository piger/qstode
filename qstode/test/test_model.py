# -*- coding: utf-8 -*-
"""
    qstode.test.test_model
    ~~~~~~~~~~~~~~~~~~~~~~

    Model and database related tests.

    :copyright: (c) 2012 by Daniel Kertesz
    :license: BSD, see LICENSE for more details.
"""
from datetime import datetime
from sqlalchemy import func
from qstode.test import FlaskTestCase
from qstode.app import db
from qstode.model.bookmark import Bookmark, Tag, Url
from qstode.model.user import User


sample_bookmarks = [
    {
        'title': u'Le facezie',
        'url': u'http://www.spatof.org',
        'tags': [u'tutorials', u'documentazione', u'zsh', u'internet'],
    },

    {
        'title': u'google',
        'url': u'http://www.google.com',
        'tags': [u'ricerca', u'internet', u'gmail', u'posta'],
    },

    {
        'title': u'Undercore',
        'url': u'http://www.undercoreonline.com',
        'tags': [u'notizie', u'articoli', u'foto', u'musica'],
    },
]

sample_users = (
    (u'pippo', u'pippo@spatof.org', 'foobar'),
    (u'pluto', u'pluto@gmail.com', 'gnagna'),
)


class UserTest(FlaskTestCase):

    def setUp(self):
        super(UserTest, self).setUp()
        self.user = User(*sample_users[0])
        self.user2 = User(*sample_users[1])

        db.session.add_all([self.user, self.user2])
        db.session.commit()

    def test_user(self):
        """User creation"""

        user = User.query.filter_by(email="pippo@spatof.org").first()
        self.assertEquals(user.email, "pippo@spatof.org")

        not_user = User.query.filter_by(email="root@example.com").first()
        self.assertEquals(not_user, None)


class TagTest(FlaskTestCase):

    def test_tag_query(self):
        """Simple SELECT Bookmark by tag(s)"""

        tag_objects = []
        for name in [u'prova', u'articoli', u'codice']:
            tag = Tag(name)
            db.session.add(tag)
            tag_objects.append(tag)

        url = Url.get_or_create(u"http://127.0.0.1")
        bookmark = Bookmark(
            title=u"titolo di prova",
            url=url,
            private=False
        )

        bookmark.tags.extend(tag_objects)
        db.session.add(bookmark)
        db.session.commit()

        b = Bookmark.query.filter(
            Bookmark.tags.any(Tag.name==u'prova'),
            ~Bookmark.tags.any(Tag.name==u'cazzo'),
        ).first()

        self.assertEquals(b.title, u"titolo di prova")

    def test_lowercase_many(self):
        """
        get_or_create_many() e lowercase

        Se si passa una Tag gia' esistente ma in case differente la funzione
        get_or_create_many() non deve creare una nuova Tag ma ritornare quella
        eisstente.
        """
        tags = [
            u'PIPPO',
            u'pluto',
            u'topolino'
        ]

        pippo = Tag(u'pippo')
        db.session.add(pippo)
        db.session.commit()

        results = Tag.get_or_create_many(tags)
        self.assertEquals(3, len(tags))
        db.session.add_all(results)
        db.session.commit()

        self.assertEquals(1,
                          len(Tag.query.filter(
                              func.lower(Tag.name) == u'pippo'
                          ).all()))
        self.assertEquals(0,
                          len(Tag.query.filter_by(name=u'PIPPO').all()))


class BookmarkTest(FlaskTestCase):
    def setUp(self):
        super(BookmarkTest, self).setUp()
        self.user = User(*sample_users[0])
        self.user2 = User(*sample_users[1])

        db.session.add_all([self.user, self.user2])
        db.session.commit()

    def test_defaults(self):
        """Default values for new Bookmark"""

        bd = sample_bookmarks[0]

        url = Url.get_or_create(bd['url'])
        b = Bookmark(bd['title'], url)
        db.session.add(b)
        db.session.commit()

        b = Bookmark.query.filter_by(title=bd['title']).first()
        self.assertIsInstance(b.creation_date, datetime)
        self.assertIsInstance(b.last_modified, datetime)

    def test_query(self):
        """SELECT Bookmark by tag(s)"""

        tag_cache = {}

        for bd in sample_bookmarks:
            url = Url.get_or_create(bd['url'])
            b = Bookmark(bd['title'], url)
            for t in bd['tags']:
                if t in tag_cache:
                    b.tags.append(tag_cache[t])
                else:
                    tag = Tag.get_or_create(t)
                    tag_cache[t] = tag
                    b.tags.append(tag)

            db.session.add(b)
        db.session.commit()

        result = Bookmark.by_tags([u'internet', u'posta'])
        self.assertEquals(result.count(), 1)

        result = Bookmark.by_tags([u'internet'])
        self.assertEquals(result.count(), 2)

        result = Bookmark.by_tags([u'internet', u'musica'])
        self.assertEquals(result.count(), 0)

        result = Bookmark.by_tags([u'ricerca', u'posta'])
        self.assertEquals(result.count(), 1)


class URLGenericTest(FlaskTestCase):
    def test_duplicates(self):
        url1 = Url(u'http://127.0.0.1')
        db.session.add(url1)
        db.session.commit()
        url1 = Url.query.filter_by(url=u'http://127.0.0.1').first()
        url2 = Url.get_or_create(u'http://127.0.0.1')
        self.assertEquals(url1, url2)
        self.assertEquals(url1.id, url2.id)
