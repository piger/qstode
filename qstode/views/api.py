# -*- coding: utf-8 -*-
"""
    qstode.views.api
    ~~~~~~~~~~~~~~~~

    Experimental RESTful JSON API.

    :copyright: (c) 2012 by Daniel Kertesz
    :license: BSD, see LICENSE for more details.
"""
from flask import jsonify, request
from flask.views import MethodView
from qstode.app import app
from qstode import db
from qstode import model


AUTOCOMPLETE_LIMIT = 15


class APIError(Exception):
    status_code = 400

    def __init__(self, message, status_code=None, payload=None):
        Exception.__init__(self)
        self.message = message
        if status_code is not None:
            self.status_code = status_code
        self.payload = payload

    def to_dict(self):
        rv = dict(self.payload or ())
        rv['message'] = self.message
        return rv


@app.errorhandler(APIError)
def handle_api_error(error):
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
    return response


class BookmarkAPI(MethodView):
    PER_PAGE = 15

    def get(self, bookmark_id=None):
        page = request.args.get("page", 1)
        try:
            page = int(page)
        except ValueError:
            raise APIError(u"Invalid page requested", status_code=404)

        if bookmark_id is None:
            bookmarks = model.Bookmark.get_latest().paginate(page, self.PER_PAGE)
            results = {
                '_pagination': {
                    '_cur_page': bookmarks.page,
                    '_next_page': bookmarks.next_num,
                    '_prev_page': bookmarks.prev_num,
                    '_num_pages': bookmarks.pages,
                },
                'bookmarks': [bk.to_dict() for bk in bookmarks.items],
            }

            return jsonify(results)
        else:
            bookmark = model.Bookmark.query.\
                       filter(model.Bookmark.id == bookmark_id).\
                       filter(model.Bookmark.private == False).\
                       first()

            if bookmark is None:
                raise APIError(u"Bookmark not found", status_code=404)
            return jsonify(bookmark=bookmark.to_dict())

bookmark_view = BookmarkAPI.as_view('bookmark_api')
app.add_url_rule('/api/bookmarks/', view_func=bookmark_view, methods=['GET',])
app.add_url_rule('/api/bookmarks/<int:bookmark_id>', view_func=bookmark_view,
                 methods=['GET'])


@app.route('/_complete/tags')
def complete_tags():
    term = request.args.get("term", u"", type=unicode)
    results = []

    if term:
        tags = model.Tag.search(term).limit(AUTOCOMPLETE_LIMIT).all()
        results.extend([dict(id=tag.id, label=tag.name, value=tag.name)
                        for tag in tags])

    return jsonify(results=results)
