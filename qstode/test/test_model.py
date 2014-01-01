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
from ..model import User, Bookmark, Tag, Link


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


class ModelTest(FlaskTestCase):
    def setUp(self):
        super(ModelTest, self).setUp()
        pippo = User(u"pippo", "pippo@example.com", "secret")
        pluto = User(u"pluto", "pluto@example.com", "secret")
        db.Session.add_all([pippo, pluto])
        db.Session.commit()

        b1 = Bookmark.create({
            'url': u"http://www.google.com",
            'title': u"Google",
            'notes': u"Google search engine",
            'tags': [u"search", u"web", u"google"],
            'user': pippo,
        })
        db.Session.add(b1)
        db.Session.commit()

        b2 = Bookmark.create({
            'url': u"http://www.bing.com",
            'title': u"Bing",
            'notes': u"Bing search engine",
            'tags': [u"search", u"web", u"bing"],
            'user': pippo,
            'private': True,
        })
        db.Session.add(b2)
        db.Session.commit()

        b3 = Bookmark.create({
            'url': u"http://www.slashdot.org",
            'title': u"Slashdot",
            'notes': u"Slashdot: news for nerds",
            'tags': [u"news", u"nerds", u"web"],
            'user': pluto,
        })
        db.Session.add(b3)
        db.Session.commit()


class UserTest(FlaskTestCase):
    def test_user_creation(self):
        user = User(u"pippo", u"pippo@example.com", "secret")
        db.Session.add(user)
        db.Session.commit()

        user = User.query.filter_by(username=u"pippo").first()
        assert user is not None
        assert user.check_password('secret') is True
        assert user.is_active() is True


class TagTest(ModelTest):
    def test_get_many(self):
        names = [u"news", u"web"]
        tags = Tag.get_many(names)
        assert [t.name for t in tags] == [u"news", u"web"]

    def test_tag_search(self):
        tag = Tag.search(u"new").first()
        assert tag.name == u"news"

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

        pippo = Tag(u'pippo')
        db.Session.add(pippo)
        db.Session.commit()

        results = Tag.get_or_create_many(tags)
        self.assertEquals(3, len(tags))
        db.Session.add_all(results)
        db.Session.commit()

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

        db.Session.add_all([self.user, self.user2])
        db.Session.commit()

    def test_defaults(self):
        """Default values for new Bookmark"""

        bd = sample_bookmarks[0]

        url = Link.get_or_create(bd['url'])
        b = Bookmark(bd['title'])
        b.link = url
        db.Session.add(b)
        db.Session.commit()

        b = Bookmark.query.filter_by(title=bd['title']).first()
        self.assertIsInstance(b.created_on, datetime)
        self.assertIsInstance(b.modified_on, datetime)

    def test_query(self):
        """SELECT Bookmark by tag(s)"""

        tag_cache = {}

        for bd in sample_bookmarks:
            url = Link.get_or_create(bd['url'])
            b = Bookmark(bd['title'])
            b.link = url
            for t in bd['tags']:
                if t in tag_cache:
                    b.tags.append(tag_cache[t])
                else:
                    tag = Tag.get_or_create(t)
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
            rv = Bookmark.by_tags(tags)
            self.assertEquals(rv.count(), count)
