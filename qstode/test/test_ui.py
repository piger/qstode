import pytest
from selenium.webdriver.common.keys import Keys
from qstode.test import FlaskTestCase


@pytest.fixture
def chrome_options(chrome_options):
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--window-size=1920x1080')
    return chrome_options


@pytest.mark.usefixtures('selenium')
class IntegrationTestCase(FlaskTestCase):
    def __init__(self, *args, **kwargs):
        super(IntegrationTestCase, self).__init__(*args, **kwargs)
        self.s = None
        self.base_url = 'http://127.0.0.1:5000'

    @pytest.fixture(autouse=True)
    def add_selenium(self, selenium):
        """Hack pytest fixtures to inject the selenium fixture in this class"""
        self.s = selenium

    def get(self, url_tail):
        return self.s.get(self.base_url + url_tail)

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
