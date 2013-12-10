# -*- coding: utf-8 -*-
"""
    qstode.views.bookmark
    ~~~~~~~~~~~~~~~~~~~~~

    Main application view definitions.

    :copyright: (c) 2012 by Daniel Kertesz
    :license: BSD, see LICENSE for more details.
"""
import re
import os
from datetime import datetime
from urlparse import urljoin
from flask import (render_template, redirect, request, flash,
                   abort, url_for, send_from_directory)
from flask_login import login_required, current_user
from flask_babel import gettext
from flask_sqlalchemy import get_debug_queries, Pagination
from werkzeug.contrib.atom import AtomFeed

from qstode.app import app, whoosh_searcher
from qstode import forms
from qstode import model
from qstode import settings
from qstode import db


# robots.txt
@app.route('/robots.txt')
def robotstxt():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'robots.txt', mimetype='text/plain')


@app.context_processor
def inject_globals():
    """Injects some useful variables in the jinja2 context"""

    if request.method == 'GET' and 'query' in request.args:
        search_form = forms.SimpleSearchForm(request.args)
    else:
        search_form = forms.SimpleSearchForm()

    return dict(
        search_form=search_form,
        taglist=model.Tag.taglist(40),
        debug_queries=get_debug_queries()
    )


@app.errorhandler(404)
def page_not_found(error):
    return render_template("404.html"), 404


@app.errorhandler(500)
def internal_error(error):
    db.Session.rollback()
    return render_template("500.html"), 500


@app.errorhandler(403)
def permission_denied(e):
    """Handle the 403 error code for permission protected pages"""
    return render_template("permission_denied.html"), 403


@app.route('/', defaults={'page': 1})
@app.route('/page/<int:page>')
def index(page):
    bookmarks = model.Bookmark.get_latest().paginate(page, settings.PER_PAGE)

    return render_template('index.html', bookmarks=bookmarks)


@app.route('/about')
def about():
    data = {
        'num_bookmarks': model.Bookmark.query.filter_by(private=False).count(),
        'num_tags': model.Tag.query.join(model.Tag.bookmarks).filter(
            model.Tag.bookmarks.any(model.Bookmark.private == False)
        ).distinct(model.Tag.name).group_by(model.Tag.id).count(),
    }

    return render_template('about.html', data=data)


@app.route('/help')
def help():
    bookmarklet_url = request.url_root
    return render_template('help.html', bookmarklet_url=bookmarklet_url)


@app.route('/tagged/<tags>/<int:page>')
@app.route('/tagged/<tags>', defaults={'page': 1})
def tagged(tags, page):
    """Shows all bookmarks tagged with one or more comma separated tags"""

    tags = re.split(r'\s*,\s*', tags)
    bookmarks = model.Bookmark.by_tags(tags).paginate(page, settings.PER_PAGE)
    related = model.Tag.get_related(tags)

    return render_template('tagged.html', bookmarks=bookmarks, tags=tags,
                           related=related)


@app.route('/u/<username>/<int:page>')
@app.route('/u/<username>', defaults={'page': 1})
def user_bookmarks(username, page):
    """Shows all bookmarks for a specific user"""

    for_user = model.User.query.filter_by(username=username).first_or_404()

    if current_user.is_authenticated() and for_user.id == current_user.id:
        include_private = True
    else:
        include_private = False

    results = model.Bookmark.by_user(for_user.id, include_private=include_private).\
              paginate(page, settings.PER_PAGE)

    return render_template('user_bookmarks.html', bookmarks=results,
                           for_user=for_user)


@app.route('/post', methods=['GET', 'POST'])
@login_required
def post_bookmark():
    """Posts a new bookmark (with a popup window)"""

    url = request.args.get('url', '')
    title = request.args.get('title', '')
    notes = request.args.get('notes', '')
    url_count = 0

    if url:
        url_count += model.Url.query.filter_by(url=url).count()

    form = forms.BookmarkForm(request.form, url=url, title=title, notes=notes)
    if form.validate_on_submit():
        bookmark = form.create_bookmark(current_user)
        db.Session.refresh(bookmark)
        whoosh_searcher.add_bookmark(bookmark)
        return redirect(url_for('close_popup'))

    return render_template('post_popup.html', form=form, url_count=url_count)


@app.route('/add', methods=['GET', 'POST'])
@login_required
def add():
    """Posts a new bookmark from the main UI"""

    url = request.args.get('url', '')
    title = request.args.get('title', '')

    form = forms.BookmarkForm(request.form, url=url, title=title)

    if form.validate_on_submit():
        bookmark = form.create_bookmark(current_user)

        db.Session.refresh(bookmark)
        whoosh_searcher.add_bookmark(bookmark)

        flash(gettext(u"Bookmark added!"), "success")
        return redirect(url_for('index'))

    return render_template('post.html', form=form)


@app.route('/close')
@login_required
def close_popup():
    return render_template('close.html')


@app.route('/edit/<bId>', methods=['GET', 'POST'])
@login_required
def edit_bookmark(bId):
    bookmark = model.Bookmark.query.filter_by(
        id=bId
    ).first()

    if (bookmark is None or bookmark.user != current_user):
        abort(404)

    form = forms.BookmarkForm.from_bookmark(bookmark, request.form)

    if form.validate_on_submit():
        if form.url.data != bookmark.href:
            new_url = model.Url.get_or_create(form.url.data)
            bookmark.url = new_url
        bookmark.title = form.title.data
        bookmark.private = form.private.data

        # We can't do something like:
        #
        # for tag in bookmark.tags:
        #       bookmark.tags.remove(tag)
        #
        # So we must resort to this trick
        tags = model.Tag.get_or_create_many(form.tags.data)
        tags_to_delete = bookmark.tags[:]
        for tag in tags_to_delete:
            bookmark.tags.remove(tag)
        bookmark.tags.extend(tags)

        bookmark.notes = form.notes.data

        db.Session.commit()
        flash(gettext(u"Bookmark modified"), 'success')

        db.Session.refresh(bookmark)
        whoosh_searcher.update_bookmark(bookmark)

        return form.redirect('index')

    return render_template('edit_bookmark.html', form=form)


@app.route('/delete/<int:bId>', methods=['GET', 'POST'])
@login_required
def delete_bookmark(bId):
    bookmark = model.Bookmark.query.get_or_404(bId)
    form = forms.RedirectForm()

    if bookmark.user.id != current_user.id:
        abort(404)

    if form.validate_on_submit():
        bk_id = bookmark.id
        db.Session.delete(bookmark)
        db.Session.commit()

        whoosh_searcher.delete_bookmark(bk_id)

        flash(gettext("Bookmark deleted"), 'success')
        return form.redirect('index')

    return render_template('delete_bookmark.html', form=form, bookmark=bookmark)


@app.route('/bookmark/<int:bookmark_id>')
def single_bookmark(bookmark_id):
    bookmark = model.Bookmark.query.get_or_404(bookmark_id)

    if bookmark.private and bookmark.user.id != current_user.id:
        abort(404)

    return render_template('single.html', bookmark=bookmark)


@app.route('/search')
def simple_search():
    """Performs a simple search from the form on the navigation bar"""
    form = forms.SimpleSearchForm(request.args)

    if form.validate_on_submit:
        try:
            page = int(form.page.data)
        except ValueError:
            page = 1

        related = None
        if not form.query.data:
            results = []
        else:
            results = model.Bookmark.by_tags(form.query.data).\
                      paginate(page, settings.PER_PAGE)
            related = model.Tag.get_related(form.query.data)

        return render_template('tag_results.html', bookmarks=results,
                               related=related)
    return redirect(url_for('index'))


@app.route('/search/advanced', methods=["GET", "POST"])
def advanced_search():
    form = forms.AdvancedSearchForm()

    if form.validate_on_submit():
        return redirect(url_for("search_results", query=form.q.data))
            
    return render_template('advanced_search.html', form=form)


@app.route('/search_results/<query>')
def search_results(query):
    page_len = 10
    page = request.args.get("page", 1)
    try:
        page = int(page)
    except ValueError:
        page = 1

    pagination = None
    results = None
    try:
        results = whoosh_searcher.search(query, page, page_len)
    except ValueError:
        abort(400)

    # XXX pagination and Whoosh aren't working as indented :(
    if results:
        # we can use all() because the list of ids in `search_results`
        # was already paginated
        bookmarks = model.Bookmark.by_ids(results).all()
        pagination = Pagination(None, page, page_len, len(results),
                                bookmarks)

    return render_template('search_results.html', bookmarks=pagination,
                           query=query)


@app.route('/tagcloud')
def tagcloud():
    tags = model.Tag.tagcloud()

    return render_template('tagcloud.html', tagcloud=tags)


@app.route('/feed/recent')
def feed_recent():
    feed = AtomFeed('QStode', feed_url=request.url,
                    url=request.url_root,
                    subtitle='Recent bookmarks')

    bookmarks = model.Bookmark.get_latest().limit(settings.FEED_NUM_ENTRIES).all()
    
    for bookmark in bookmarks:
        item_id = urljoin(request.url_root,
                          url_for('single_bookmark', bookmark_id=bookmark.id))

        feed.add(title=bookmark.title,
                 title_type='text',
                 content=unicode(bookmark.notes),
                 content_type='text',
                 author=bookmark.user.username,
                 url=bookmark.href,
                 updated=bookmark.modified_on,
                 published=bookmark.created_on,
                 id=item_id)

    return feed.get_response()


@app.route('/export_bookmarks')
@login_required
def export_bookmarks():
    bookmarks = model.Bookmark.by_user(current_user.id, include_private=True)
    today = datetime.now()
    return render_template('_export.html', bookmarks=bookmarks, today=today)
