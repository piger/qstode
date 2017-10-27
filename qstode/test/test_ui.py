import os
import tempfile
import shutil
from flask_testing import LiveServerTestCase
import pytest
from selenium.webdriver.common.keys import Keys
from qstode import main
from qstode import db


@pytest.fixture
def chrome_options(chrome_options):
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--window-size=1920x1080')
    return chrome_options


@pytest.mark.usefixtures('selenium')
class IntegrationTestCase(LiveServerTestCase):
    def __init__(self, *args, **kwargs):
        super(IntegrationTestCase, self).__init__(*args, **kwargs)
        self.s = None

    def create_app(self):
        self.tmp_dir = tempfile.mkdtemp()
        self.db_filename = os.path.join(self.tmp_dir, "db.sqlite")

        config = {
            # I hate the author of Flask-WTF for changing the name of the
            # configuration parameter.
            'WTF_CSRF_ENABLED': False,
            'CSRF_ENABLED': False,
            'SQLALCHEMY_DATABASE_URI': "sqlite:///%s" % self.db_filename,
            'SECRET_KEY': 'test',
            'TESTING': True,
            'LIVESERVER_PORT': 5123,
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

    @pytest.fixture(autouse=True)
    def add_selenium(self, selenium):
        """Hack pytest fixtures to inject the selenium fixture in this class"""
        self.s = selenium

    def get(self, url_tail):
        return self.s.get(self.get_server_url() + url_tail)

    def test_home(self):
        self.get('/')
        assert "QStode" in self.s.page_source

        search_box = self.s.find_element_by_id("query")
        search_box.send_keys("suca")
        search_box.send_keys(Keys.RETURN)
        assert "No matching bookmark was found." in self.s.page_source

    def test_reset(self):
        self.get('/user/reset/request')
        assert "If you have lost your password you can request a reset" in self.s.page_source
