# -*- coding: utf-8 -*-
"""
    qstode.test.test_forms
    ~~~~~~~~~~~~~~~~~~~~~~

    Unit tests related to forms.

    :copyright: (c) 2012 by Daniel Kertesz
    :license: BSD, see LICENSE for more details.
"""
from wtforms import Form
from wtforms.fields import StringField
from flask import url_for, g
from mock import patch
from werkzeug.datastructures import MultiDict
from .. import test
from .. import model
from .. import forms
from ..forms.validators import *


SAMPLE_DATA = {
    'title': "A Test title",
    'url': "http://www.example.com",
    'private': False,
    'tags': "test, form validation, mordor",
    'notes': "A couple of notes",
}


class ValidatorsTest(test.FlaskTestCase):
    def setUp(self):
        super(ValidatorsTest, self).setUp()
        self._load_data([
            model.User('pippo', 'pippo@example.com', 'secret')
        ])

    def test_unique_username_ok(self):
        """Validation: unique username"""

        class TestForm(Form):
            username = StringField("username", [unique_username()])

        form = TestForm(username="charlie_root")
        self.assertTrue(form.validate())

    def test_unique_username_fail(self):
        """Failed validation: unique username"""

        class TestForm(Form):
            username = StringField("username", [unique_username()])

        form = TestForm(username="pippo")
        self.assertFalse(form.validate())

    def test_unique_email_ok(self):
        """Validation: unique email address"""

        class TestForm(Form):
            email = StringField("email", [unique_email()])

        form = TestForm(email="charlie@root.com")
        self.assertTrue(form.validate())

    def test_unique_email_fail(self):
        """Failed validation: unique email address"""

        class TestForm(Form):
            email = StringField("email", [unique_email()])

        form = TestForm(email="pippo@example.com")
        self.assertFalse(form.validate())


class BookmarkFormBaseTest(test.FlaskTestCase):
    def setUp(self):
        super(BookmarkFormBaseTest, self).setUp()
        self._load_data([
            model.User('pippo', 'pippo@example.com', 'secret')
        ])

    def _login(self):
        rv = self.client.post('/login', data={
            "user": "pippo@example.com",
            "password": "secret"
        }, follow_redirects=False)
        self.assert_redirects(rv, url_for('index'))


class BookmarkFormTest(BookmarkFormBaseTest):

    def test_submit_bookmark(self):
        """Bookmark form submission"""

        self._login()

        rv = self.client.post('/add', data=SAMPLE_DATA)
        self.assertTrue(rv.status_code in (301, 302), "Got %r instead (%r)" % (rv.status_code, rv.data))
        self.assert_redirects(rv, url_for('index'))

        b = model.Bookmark.query.filter_by(title=SAMPLE_DATA['title']).first()
        self.assertIsNotNone(b, "Non e' stato creato il Bookmark")
        self.assertEqual(b.href, SAMPLE_DATA['url'])

    def test_missing_fields(self):
        """Failed validation of Bookmark submission with missing fields"""

        self._login()
        for field in ('tags', 'title', 'url'):
            data = SAMPLE_DATA.copy()
            data.pop(field)
            rv = self.client.post('/add', data=data)
            self.assert200(rv)
            res = "field is required" in rv.data or "Invalid URL" in rv.data
            self.assertTrue(res, rv.data)

    def test_notes_validation(self):
        self._login()
        data = SAMPLE_DATA.copy()
        data['notes'] = "A" * (model.NOTES_MAX + 1)

        rv = self.client.post(url_for('add'), data=data)
        self.assert200(rv)


class TagListTest(BookmarkFormBaseTest):
    def test_empty_values(self):
        """Validation of empty values as tag list (i.e. ",,,")"""

        class TestForm(Form):
            tags = forms.TagListField()
            
        with self.app.test_request_context():
            data = MultiDict([
                ("tags", "fast, lazy, , ,,,"),
            ])
            form = TestForm(data)
            self.assertTrue(form.validate())
            self.assertEqual(form.tags.data, ['fast', 'lazy'])

    def test_taglist_duplicates(self):
        """Duplicate and mixed-case handling of TagList field"""

        self._login()
        rv = self.client.post('/add', data={
            'title': 'Un titolo',
            'url': 'http://www.google.it',
            'private': False,
            'tags': "uno, uno, UNO, uNo, UnO",
            'notes': ''
        })
        self.assert_redirects(rv, url_for('index'))

        b = model.Bookmark.query.filter_by(title='Un titolo').first()
        self.assertIsNotNone(b, "Non e' stato creato il Bookmark")
        self.assertEqual(b.href, 'http://www.google.it')
        tags = [tag.name for tag in b.tags]
        assert len(tags) == 1
        assert tags[0] == "uno"

    def test_length_validator_exceed(self):
        """Validation of maximum number of tags for TagList field"""

        self._login()
        data = SAMPLE_DATA.copy()
        tags = ', '.join(["tag-%d" % i for i in range(forms.TAGLIST_MAX + 1)])
        data['tags'] = tags
        rv = self.client.post('/add', data=data)
        self.assertEqual(rv.status_code, 200)

    def test_length_validator_correct(self):
        """Validation of Bookmark submission"""

        self._login()
        data = SAMPLE_DATA.copy()
        tags = ', '.join(["tag-%d" % i for i in range(49)])
        data['tags'] = tags
        rv = self.client.post('/add', data=data)
        self.assertTrue(rv.status_code in (301, 302), "Got %r instead (%r)" % (rv.status_code, rv.data))
        self.assert_redirects(rv, url_for('index'))


class LoginFormTest(test.FlaskTestCase):
    """LoginForm and RedirectForm unit testing"""

    def test_empty_form(self):
        """Validation of a form with empty fields"""

        with self.app.test_request_context():
            g.lang = "en"
            form = forms.LoginForm()
            self.assertFalse(form.validate())

    def test_required_fields(self):
        """Validation of required fields"""
        with self.app.test_request_context():
            g.lang = "en"

            data = MultiDict([
                ('user', 'user@example.com'),
                ('password', 'secret'),
            ])
            form = forms.LoginForm(data)
            self.assertTrue(form.validate())


class PasswordChangeFormTest(test.FlaskTestCase):
    def test_failed_validation(self):
        with self.app.test_request_context():
            g.lang = "en"
            data = MultiDict([
                ('password', ''),
                ('password_confirm', '')])
            form = forms.PasswordChangeForm(data)
            self.assertFalse(form.validate())

    def test_successful_validation(self):
        with self.app.test_request_context():
            g.lang = "en"
            data = MultiDict([
                ('password', 'abcd1234'),
                ('password_confirm', 'abcd1234')])
            form = forms.PasswordChangeForm(data)
            self.assertTrue(form.validate())

    def test_short_password(self):
        with self.app.test_request_context():
            g.lang = "en"
            data = MultiDict([
                ('password', 'abcd'),
                ('password_confirm', 'abcd')])
            form = forms.PasswordChangeForm(data)
            self.assertFalse(form.validate())
