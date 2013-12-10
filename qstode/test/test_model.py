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
from nose.plugins.skip import SkipTest
from qstode.test import FlaskTestCase
from qstode import db
from qstode import model


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
        self.user = model.User(*sample_users[0])
        self.user2 = model.User(*sample_users[1])

        db.Session.add_all([self.user, self.user2])
        db.Session.commit()

    def test_user(self):
        """User creation"""

        user = model.User.query.filter_by(email="pippo@spatof.org").first()
        self.assertEquals(user.email, "pippo@spatof.org")

        not_user = model.User.query.filter_by(email="root@example.com").first()
        self.assertEquals(not_user, None)


class TagTest(FlaskTestCase):

    def test_tag_query(self):
        """Simple SELECT Bookmark by tag(s)"""

        tag_objects = []
        for name in [u'prova', u'articoli', u'codice']:
            tag = model.Tag(name)
            db.Session.add(tag)
            tag_objects.append(tag)

        url = model.Link.get_or_create(u"http://127.0.0.1")
        bookmark = model.Bookmark(title=u"titolo di prova", private=False)
        bookmark.link = url

        bookmark.tags.extend(tag_objects)
        db.Session.add(bookmark)
        db.Session.commit()

        b = model.Bookmark.query.filter(
            model.Bookmark.tags.any(model.Tag.name==u'prova'),
            ~model.Bookmark.tags.any(model.Tag.name==u'cazzo'),
        ).first()

        self.assertEquals(b.title, u"titolo di prova")

    def test_lowercase_many(self):
        """
        get_or_create_many() e lowercase

        Se si passa una Tag gia' esistente ma in case differente la funzione
        get_or_create_many() non deve creare una nuova Tag ma ritornare quella
        eisstente.
        """

        raise SkipTest("Must be updated to support orphan tag deletion")

        tags = [
            u'PIPPO',
            u'pluto',
            u'topolino'
        ]

        pippo = model.Tag(u'pippo')
        db.Session.add(pippo)
        db.Session.commit()

        results = model.Tag.get_or_create_many(tags)
        self.assertEquals(3, len(tags))
        db.Session.add_all(results)
        db.Session.commit()

        self.assertEquals(1,
                          len(model.Tag.query.filter(
                              func.lower(model.Tag.name) == u'pippo'
                          ).all()))
        self.assertEquals(0,
                          len(model.Tag.query.filter_by(name=u'PIPPO').all()))


class BookmarkTest(FlaskTestCase):
    def setUp(self):
        super(BookmarkTest, self).setUp()
        self.user = model.User(*sample_users[0])
        self.user2 = model.User(*sample_users[1])

        db.Session.add_all([self.user, self.user2])
        db.Session.commit()

    def test_defaults(self):
        """Default values for new Bookmark"""

        bd = sample_bookmarks[0]

        url = model.Link.get_or_create(bd['url'])
        b = model.Bookmark(bd['title'])
        b.link = url
        db.Session.add(b)
        db.Session.commit()

        b = model.Bookmark.query.filter_by(title=bd['title']).first()
        self.assertIsInstance(b.created_on, datetime)
        self.assertIsInstance(b.modified_on, datetime)

    def test_query(self):
        """SELECT Bookmark by tag(s)"""

        tag_cache = {}

        for bd in sample_bookmarks:
            url = model.Link.get_or_create(bd['url'])
            b = model.Bookmark(bd['title'])
            b.link = url
            for t in bd['tags']:
                if t in tag_cache:
                    b.tags.append(tag_cache[t])
                else:
                    tag = model.Tag.get_or_create(t)
                    tag_cache[t] = tag
                    b.tags.append(tag)

            db.Session.add(b)
        db.Session.commit()

        test_data = [
            ([u"internet", u"posta"], 1),
            ([u"internet"], 2),
            ([u"internet", u"musica"], 0),
            ([u"ricerca", u"posta"], 1)]

        for tags, count in test_data:
            rv = model.Bookmark.by_tags(tags)
            self.assertEquals(rv.count(), count)


class URLGenericTest(FlaskTestCase):
    def test_duplicates(self):
        url1 = model.Link(href=u'http://127.0.0.1')
        db.Session.add(url1)
        db.Session.commit()
        url1 = model.Link.query.filter_by(href=u'http://127.0.0.1').first()
        url2 = model.Link.get_or_create(u'http://127.0.0.1')
        self.assertEquals(url1, url2)
        self.assertEquals(url1.id, url2.id)
