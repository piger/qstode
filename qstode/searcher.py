# -*- coding: utf-8 -*-
"""
    qstode.searcher
    ~~~~~~~~~~~~~~~

    Whoosh search engine support.

                           *** ALPHA VERSION ***

    At the moment this module must be disabled in the testing environment
    because we use an `AsyncWriter` by default to write out changes to the
    search index and this does not cope well with the tests setup
    (i.e. the search index is deleted after each test run).

    :copyright: (c) 2012 by Daniel Kertesz
    :license: BSD, see LICENSE for more details.
"""
import os
from whoosh.fields import ID, TEXT, KEYWORD, DATETIME, Schema
from whoosh.analysis import RegexTokenizer, LowercaseFilter, CharsetFilter
from whoosh.support.charset import accent_map
from whoosh.index import create_in, open_dir, exists_in
from whoosh.writing import AsyncWriter
from whoosh.qparser import MultifieldParser
from whoosh.sorting import Facets
from . import exc


def generate_schema():
    text_analyzer = RegexTokenizer() \
                    | LowercaseFilter() \
                    | CharsetFilter(accent_map)

    schema = Schema(id=ID(stored=True, unique=True),
                    title=TEXT(stored=False, analyzer=text_analyzer),
                    tags=KEYWORD(stored=False, lowercase=True, commas=True),
                    notes=TEXT(stored=False, analyzer=text_analyzer),
                    date=DATETIME(stored=False))
    return schema


class WhooshSearcher(object):
    def __init__(self, app=None, index_dir=None):
        self.app = app
        self.index_dir = index_dir
        self._ix = None

    @property
    def ix(self):
        if self._ix is None:
            self._ix = self._open_index()
        return self._ix

    def init_app(self, app):
        """Initialize module and checks if the index exists"""

        self.app = app
        if not 'WHOOSH_INDEX_PATH' in self.app.config:
            raise exc.InitializationError("You must set the WHOOSH_INDEX_PATH option in the configuration")
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

    def add_bookmark(self, bookmark, writer=None):
        doc = {
            'id': unicode(bookmark.id),
            'tags': u", ".join([t.name for t in bookmark.tags]),
            'title': bookmark.title or u'',
            'notes': bookmark.notes or u'',
        }
        if writer is None:
            writer = self.get_async_writer()
            writer.update_document(**doc)
            writer.commit()
        else:
            writer.update_document(**doc)

    def update_bookmark(self, bookmark, writer=None):
        self.add_bookmark(bookmark, writer)
        
    def delete_bookmark(self, bookmark_id, writer=None):
        bookmark_id = unicode(bookmark_id)

        if writer is None:
            writer = self.get_async_writer()
            writer.delete_by_term("id", bookmark_id)
            writer.commit()
        else:
            writer.delete_by_term("id", bookmark_id)

    def search(self, query, page=1, page_len=10,
               fields=('notes', 'title', 'tags')):
        """Perform a search.

        :return: a list of bookmark id
        :rtype: list of ints
        """
        results = []

        with self.ix.searcher() as searcher:
            parser = MultifieldParser(fields, self.ix.schema)
            whoosh_query = parser.parse(query)
            facets = Facets()
            facets.add_field('tags', allow_overlap=True)

            # this can raise a ValueError
            search_results = searcher.search_page(whoosh_query, page,
                                                  pagelen=page_len,
                                                  groupedby=facets)
            results.extend([int(result['id']) for result in search_results])

        return results
