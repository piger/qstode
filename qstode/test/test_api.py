"""
    qstode.test.test_api
    ~~~~~~~~~~~~~~~~~~~~

    REST API testing.

    :copyright: (c) 2012 by Daniel Kertesz
    :license: BSD, see LICENSE for more details.
"""
from flask import url_for
from . import FlaskTestCase
from .model_factory import UserFactory, TagFactory, BookmarkFactory
from .. import db


class ApiTestBase(FlaskTestCase):
    def setUp(self):
        super(ApiTestBase, self).setUp()
        self.user1 = UserFactory.create(username="user1", password="password")
        self.user2 = UserFactory.create(username="user2", password="password")
        db.Session.commit()

        BookmarkFactory.create(
            user=self.user1,
            tags=[TagFactory.create(name=w) for w in ("programming", "python", "guido")],
        )
        db.Session.commit()

        BookmarkFactory.create(
            user=self.user1,
            tags=[TagFactory.create(name=w) for w in ("web", "python", "tags", "flask")],
        )
        db.Session.commit()


class TaglistViewTest(ApiTestBase):
    def test_taglist(self):
        rv = self.client.get(url_for("api_taglist"))
        self.assert200(rv)
        self.assertEqual(rv.mimetype, "application/json")

        # most popular tag will be "python"
        tags = rv.json.get("tags", [])
        first = tags[0]
        self.assertEqual(first["tag"], "python")
        self.assertEqual(len(tags), 6)
