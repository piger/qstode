"""
    qstode.test.test_frontend_views
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    General views testing.

    :copyright: (c) 2012 by Daniel Kertesz
    :license: BSD, see LICENSE for more details.
"""
from flask import url_for
from . import FlaskTestCase
from .. import db
from ..model.user import User
from ..model.bookmark import Bookmark
from .model_factory import UserFactory


class FrontendViewsTest(FlaskTestCase):
    def setUp(self):
        super(FrontendViewsTest, self).setUp()
        user_1 = User("user1", "user1@example.com", "password")
        user_2 = User("user2", "user2@example.com", "password")

        db.Session.add_all([user_1, user_2])
        db.Session.commit()

        b1 = Bookmark.create(
            {
                "url": "http://www.python.org",
                "title": "Python",
                "notes": "Python website",
                "tags": ["programming", "python", "guido"],
                "user": user_1,
            }
        )
        db.Session.add(b1)
        db.Session.commit()

        b2 = Bookmark.create(
            {
                "url": "https://github.com/piger/qstode",
                "title": "QStode",
                "notes": "QStode source code",
                "tags": ["web", "python", "tags", "flask"],
                "user": user_1,
            }
        )
        db.Session.add(b2)
        db.Session.commit()

    def test_index_content(self):
        rv = self.client.get(url_for("index"))
        self.assert200(rv)
        assert b"Python website" in rv.data

    def test_login_failure(self):
        form_data = {"user": "not_user", "password": "password", "next": url_for("index")}
        rv = self.client.post(url_for("login"), data=form_data)
        self.assert200(rv)

    def test_login_success(self):
        form_data = {"user": "user1", "password": "password", "next": url_for("index")}
        rv = self.client.post(url_for("login"), data=form_data)
        self.assert_redirects(rv, url_for("index"))

    def test_complete_tags_success(self):
        rv = self.client.get(url_for("complete_tags") + "?term=pyt")
        self.assert200(rv)
        self.assertTrue("results" in rv.json)

        results = rv.json.get("results", [])
        assert len(results) == 1
        assert results[0].get("value", "") == "python"

    def test_complete_tags_empty(self):
        expected = {"results": []}
        rv = self.client.get(url_for("complete_tags") + "?term=foobarbaz")
        self.assert200(rv)
        self.assertEqual(rv.json, expected)


class AdminViewsTest(FlaskTestCase):
    def setUp(self):
        super(AdminViewsTest, self).setUp()

        self.admin = UserFactory.create(username="admin", password="secret", admin=True)
        self.user = UserFactory.create(password="hunter2")
        UserFactory.create_batch(10)
        db.Session.commit()

    def admin_login(self):
        form = {"user": "admin", "password": "secret", "next": url_for("index")}
        result = self.client.post(url_for("login"), data=form)
        self.assert_redirects(result, url_for("index"))

    def user_login(self):
        form = {"user": self.user.username, "password": "hunter2", "next": url_for("index")}
        result = self.client.post(url_for("login"), data=form)
        self.assert_redirects(result, url_for("index"))

    def test_access_denied(self):
        views = ("admin_users", "admin_create_user")

        # non authenticated
        for view in views:
            result = self.client.get(url_for(view))
            self.assert403(result)

        result = self.client.get(url_for("admin_delete_user", user_id=1))
        self.assert403(result)
        result = self.client.get(url_for("admin_edit_user", user_id=1))
        self.assert403(result)

        # authenticated as normal user
        self.user_login()
        for view in views:
            result = self.client.get(url_for(view))
            self.assert403(result)

        result = self.client.get(url_for("admin_delete_user", user_id=1))
        self.assert403(result)
        result = self.client.get(url_for("admin_edit_user", user_id=1))
        self.assert403(result)

    def test_list_users(self):
        self.admin_login()
        result = self.client.get(url_for("admin_users"))
        self.assert200(result)
