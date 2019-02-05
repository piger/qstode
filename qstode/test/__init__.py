import os
import tempfile
import shutil
from flask_testing import TestCase
from qstode import main
from qstode import db


class FlaskTestCase(TestCase):
    def create_app(self):
        self.tmp_dir = tempfile.mkdtemp()
        self.db_filename = os.path.join(self.tmp_dir, "db.sqlite")

        config = {
            # I hate the author of Flask-WTF for changing the name of the
            # configuration parameter.
            "WTF_CSRF_ENABLED": False,
            "CSRF_ENABLED": False,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///%s" % self.db_filename,
            "SECRET_KEY": "test",
            "TESTING": True,
        }

        return main.create_app(config)

    def setUp(self):
        db.create_all()

    def tearDown(self):
        db.Session.remove()
        db.drop_all()
        shutil.rmtree(self.tmp_dir)

    def _load_data(self, data):
        for item in data:
            db.Session.add(item)
        db.Session.commit()
