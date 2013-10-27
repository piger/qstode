# -*- coding: utf-8 -*-
import os
import tempfile
import shutil
from flask_testing import TestCase
from qstode.app import db
from qstode import main


class FlaskTestCase(TestCase):
    def create_app(self):
        self.tmp_dir = tempfile.mkdtemp()
        self.db_filename = os.path.join(self.tmp_dir, "db.sqlite")
        self.whoosh_dir = os.path.join(self.tmp_dir, "whoosh")
        self.oid_dir = os.path.join(self.tmp_dir, "oid")

        config = {
            # I hate the author of Flask-WTF for changing the name of the
            # configuration parameter.
            'WTF_CSRF_ENABLED': False,
            'CSRF_ENABLED': False,
            'SQLALCHEMY_DATABASE_URI': "sqlite:///%s" % self.db_filename,
            'WHOOSH_INDEX_PATH': self.whoosh_dir,
            'OPENID_FS_STORE_PATH': self.oid_dir,
            'SECRET_KEY': 'test',
            'HASHIDS_SECRET_KEY': 'test',
            'HASHIDS_MIN_LENGTH': 3,
            'TESTING': True,
        }

        return main.create_app(config)

    def setUp(self):
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        shutil.rmtree(self.tmp_dir)

    def _load_data(self, data):
        for item in data:
            db.session.add(item)
        db.session.commit()
