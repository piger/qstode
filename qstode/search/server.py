# -*- coding: utf-8 -*-
"""
    qstode.search.server
    ~~~~~~~~~~~~~~~~~~~~

    Whoosh search engine backend component.

    :copyright: (c) 2013 by Daniel Kertesz
    :license: BSD, see LICENSE for more details.
"""
import logging
import json
import redis
from datetime import datetime
from flask.config import Config
from qstode import db
from qstode import searcher
from qstode import model


log = logging.getLogger(__name__)


class IndexerDaemon(object):
    def __init__(self):
        self.config = Config(root_path="/")
        self.config.from_envvar('APP_CONFIG')

        self.redis = searcher.redis_connect(self.config)
        db.init_db(self.config['SQLALCHEMY_DATABASE_URI'])
        self.searcher = searcher.WhooshSearcher(
            index_dir=self.config['WHOOSH_INDEX_PATH'])

    def _get_writer(self):
        return self.searcher.ix.writer()

    def main_loop(self):
        running = True
        while running:
            self.work_on_queue()

    def work_on_queue(self):
        """Queue operations (redis reliable queue pattern)

        Atomically pop an item from the work queue and put it on the
        processing queue; after processing the item is removed from
        the processing queue.

        The "processing" step fetch the specified bookmark from the SQL
        database and run the specified operation (index, update, delete);
        after completing the operation it updates the bookmark `indexed_on`
        field.
        """
        conn = self.redis
        msg = conn.brpoplpush(searcher.QUEUE_INDEX, searcher.QUEUE_WORK)
        log.debug("Processing new operation: {}".format(msg))

        try:
            payload = json.loads(msg)
            op, _id = payload
        except ValueError, ex:
            log.debug("Invalid job in queue: {0}: {1}".format(msg, str(ex)))
        else:
            self.process(op, _id)

        conn.lrem(searcher.QUEUE_WORK, msg, 1)
        log.debug("Operation on {} completed".format(msg))

    def process(self, op, _id):
        """Operations dispatcher"""

        if op == searcher.OP_INDEX:
            self.do_index(_id)
        elif op == searcher.OP_UPDATE:
            self.do_update(_id)
        elif op == searcher.OP_DELETE:
            self.do_delete(_id)
        else:
            log.error("Invalid op: '{}'".format(op))
            
    def do_index(self, _id):
        """Index the specified bookmark id"""

        bookmark = model.Bookmark.query.get(_id)
        writer = self._get_writer()
        self.searcher.add_bookmark(bookmark, writer)

        bookmark.indexed_on = datetime.utcnow()
        db.Session.commit()

    def do_update(self, _id):
        """Updates index for the specified bookmark id"""

        self.do_index(_id)

    def do_delete(self, _id):
        """Deletes the specified bookmark id from the index"""

        writer = self._get_writer()
        self.searcher.delete_bookmark(_id, writer)


def main():
    """Daemon entry point"""

    logging.basicConfig()
    logging.getLogger().setLevel(logging.DEBUG)
    srv = IndexerDaemon()
    try:
        srv.main_loop()
    except KeyboardInterrupt:
        print "Interrupt"


if __name__ == '__main__':
    main()
