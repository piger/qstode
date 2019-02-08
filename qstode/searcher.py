"""
    qstode.searcher
    ~~~~~~~~~~~~~~~

    Whoosh search engine support.

    :copyright: (c) 2013 by Daniel Kertesz
    :license: BSD, see LICENSE for more details.
"""
import os
import json
import redis
from whoosh.fields import ID, TEXT, KEYWORD, Schema
from whoosh.analysis import RegexTokenizer, LowercaseFilter, CharsetFilter
from whoosh.support.charset import accent_map
from whoosh.index import create_in, open_dir, exists_in
from whoosh.writing import AsyncWriter
from whoosh.qparser import MultifieldParser
from whoosh.sorting import Facets


# Constants used in the Redis message queue
OP_INDEX, OP_UPDATE, OP_DELETE = list(range(3))

# Queue names for Redis
QUEUE_INDEX = "index_in"
QUEUE_WORK = "index_work"


def generate_schema():
    """Generates the search engine schema"""

    text_analyzer = RegexTokenizer() | LowercaseFilter() | CharsetFilter(accent_map)

    schema = Schema(
        id=ID(stored=True, unique=True),
        title=TEXT(stored=False, analyzer=text_analyzer),
        tags=KEYWORD(stored=False, lowercase=True, commas=True),
        notes=TEXT(stored=False, analyzer=text_analyzer),
    )
    return schema


def create_document(bookmark):
    """Creates a Document (a dict) for the search engine"""

    return {
        "id": str(bookmark.id),
        "title": bookmark.title or "",
        "notes": bookmark.notes or "",
        "tags": ", ".join([tag.name for tag in bookmark.tags]),
    }


def redis_connect(config):
    """Connects to a Redis database as specified by the dictionary `config`"""

    return redis.Redis(
        host=config.get("REDIS_HOST", "localhost"),
        port=config.get("REDIS_PORT", 6379),
        db=config.get("REDIS_DB", 0),
        password=config.get("REDIS_PASSWORD"),
    )


class WhooshSearcher(object):
    """Interface to a Whoosh based Search Engine"""

    # default search fields for user queries
    search_fields = ("notes", "title", "tags")

    def __init__(self, app=None, index_dir=None):
        self.app = app
        self.index_dir = index_dir
        self._ix = None
        self._redis = None

    @property
    def ix(self):
        """Lazy opening of the Whoosh index"""

        if self._ix is None:
            self._ix = self._open_index()
        return self._ix

    @property
    def redis(self):
        """Lazy opening of the Redis connection"""

        if self._redis is None:
            self._redis = redis_connect(self.app.config)
        return self._redis

    def init_app(self, app):
        """Initialize module and checks if the index exists"""

        self.app = app
        if "WHOOSH_INDEX_PATH" not in self.app.config:
            raise Exception("You must set the WHOOSH_INDEX_PATH option " "in the configuration")
        self.index_dir = self.app.config["WHOOSH_INDEX_PATH"]
        if not exists_in(self.index_dir):
            self.setup_index()

    def setup_index(self):
        """Create the index directory"""

        if not os.path.exists(self.index_dir):
            os.mkdir(self.index_dir)
        schema = generate_schema()
        self._ix = create_in(self.index_dir, schema)

    def _open_index(self):
        ix = open_dir(self.index_dir)
        return ix

    def get_async_writer(self):
        """Return an AsyncWriter; NOTE that we NEED thread support (i.e when
        you're running in uwsgi"""
        return AsyncWriter(self.ix)

    def push_add_bookmark(self, bookmark):
        """Pushes a 'add bookmark' operation to the Redis queue"""

        r = self.redis
        payload = json.dumps((OP_INDEX, bookmark.id))
        r.rpush(QUEUE_INDEX, payload)

    def push_update_bookmark(self, bookmark):
        """Pushes a 'update bookmark' operation to the Redis queue"""
        self.push_add_bookmark(bookmark)

    def push_delete_bookmark(self, bookmark_id):
        """Pushes a 'delete bookmark' operation to the Redis queue"""
        r = self.redis
        payload = json.dumps((OP_DELETE, bookmark_id))
        r.rpush(QUEUE_INDEX, payload)

    def add_bookmark(self, bookmark, writer=None):
        """Index a bookmark, updating it if it's already indexed;
        if you pass a `writer` object you are responsible for calling
        `commit()` at the end of the operations.
        If no `writer` is passed an AsyncWriter will be used.
        """

        document = create_document(bookmark)
        if writer is None:
            writer = self.get_async_writer()
            writer.update_document(**document)
            writer.commit()
        else:
            writer.update_document(**document)

    def update_bookmark(self, bookmark, writer=None):
        """Reindex a Bookmark"""

        self.add_bookmark(bookmark, writer)

    def delete_bookmark(self, bookmark_id, writer=None):
        """Delete a Bookmark from the index"""

        _id = str(bookmark_id)

        if writer is None:
            writer = self.get_async_writer()
            writer.delete_by_term("id", _id)
            writer.commit()
        else:
            writer.delete_by_term("id", _id)

    def search(self, query, page=1, page_len=10, fields=None):
        """Returns the results of a search engine query ordered by
        Whoosh default ordering (?).

        :returns: a list of bookmark id (int)
        """
        if fields is None:
            fields = tuple(self.search_fields)

        results = None
        with self.ix.searcher() as searcher:
            parser = MultifieldParser(fields, self.ix.schema)
            whoosh_query = parser.parse(query)
            facets = Facets()
            facets.add_field("tags", allow_overlap=True)

            # this can raise a ValueError
            search_results = searcher.search_page(
                whoosh_query, page, pagelen=page_len, groupedby=facets
            )
            results = [int(result["id"]) for result in search_results]

        return results or []
