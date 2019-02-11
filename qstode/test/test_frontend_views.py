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
from .model_factory import UserFactory, TagFactory, BookmarkFactory
from ..model.user import User


class FrontendViewsTest(FlaskTestCase):
    def setUp(self):
        super(FrontendViewsTest, self).setUp()
        self.user1 = UserFactory.create(username="user1", password="password")
        self.user2 = UserFactory.create(username="user2", password="password")
        db.Session.commit()

        self.b1 = BookmarkFactory.create(
            user=self.user1,
            tags=[TagFactory.create(name=w) for w in ("programming", "python", "guido")],
        )
        db.Session.commit()

        BookmarkFactory.create(
            user=self.user1,
            private=True,
            tags=[TagFactory.create(name=w) for w in ("web", "python", "tags", "flask")],
        )
        db.Session.commit()

    def test_index_content(self):
        rv = self.client.get(url_for("index"))
        self.assert200(rv)
        self.assertTrue(self.b1.title in rv.data.decode("utf-8"))

    def test_login_failure(self):
        form_data = {"user": "not_user", "password": "password", "next": url_for("index")}
        rv = self.client.post(url_for("login"), data=form_data)
        self.assert200(rv)

    def test_login_success(self):
        form_data = {"user": "user1", "password": "password", "next": url_for("index")}
        rv = self.client.post(url_for("login"), data=form_data)
        self.assert_redirects(rv, url_for("index"))

    def test_access_denied(self):
        result = self.client.get(url_for("user_details"))
        self.assert200(result)
        self.assertTrue("Authentication required" in result.data.decode("utf-8"))
        self.assertTemplateUsed("unauthenticated.html")

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

    def test_user_registration(self):
        form = {
            "display_name": "Piffero Pippo",
            "username": "pippo",
            "email": "pippo@pippolandia.pip",
            "password": "oh-yuk!1234",
            "password_confirm": "oh-yuk!1234",
        }
        result = self.client.post(url_for("register_user"), data=form)
        self.assertRedirects(result, url_for("login"))

        user = User.query.filter_by(username="pippo").one()
        self.assertEqual(user.display_name, "Piffero Pippo")

    def test_user_registration_short_password(self):
        """Fail user registration when a short password is supplied

        TODO: improve the test.
        """
        form = {
            "display_name": "Piffero Pippo",
            "username": "pippo",
            "email": "pippo@pippolandia.pip",
            "password": "abc",
            "password_confirm": "abc",
        }
        result = self.client.post(url_for("register_user"), data=form)
        self.assert200(result)


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
