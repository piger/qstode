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
from urllib.parse import urljoin
from flask import (render_template, redirect, request, flash,
                   abort, url_for, send_from_directory,
                   make_response)
from flask_login import login_required, current_user
from flask_babel import gettext, format_datetime
from werkzeug.contrib.atom import AtomFeed

from qstode.app import app
from qstode import forms
from qstode import model
from qstode import db
from qstode.views import helpers


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

    return dict(search_form=search_form,
                taglist=model.Tag.taglist(app.config['TAGLIST_ITEMS']))


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
    bookmarks = model.Bookmark.get_latest().\
                paginate(page, app.config['PER_PAGE'])

    return render_template('index.html', bookmarks=bookmarks)


@app.route('/about')
def about():
    data = dict(list(zip(('num_bookmarks', 'num_tags'), model.get_stats())))
    return render_template('about.html', data=data)


@app.route('/help')
def help():
    return render_template('help.html')


@app.route('/tagged/<tags>/<int:page>')
@app.route('/tagged/<tags>', defaults={'page': 1})
def tagged(tags, page):
    """Shows all bookmarks tagged with one or more comma separated tags"""

    tags = re.split(r'\s*,\s*', tags)

    # 'p' is for 'personal'
    if 'p' in request.args and current_user.is_authenticated:
        bookmarks = model.Bookmark.by_tags_user(tags, current_user.id)
    else:
        bookmarks = model.Bookmark.by_tags(tags)

    bookmarks = bookmarks.paginate(page, app.config['PER_PAGE'])

    if app.config['ENABLE_RELATED_TAGS']:
        related = model.Tag.get_related(tags)
    else:
        related = []

    return render_template('tagged.html', bookmarks=bookmarks, tags=tags,
                           related=related)


@app.route('/u/<username>/<int:page>')
@app.route('/u/<username>', defaults={'page': 1})
def user_bookmarks(username, page):
    """Shows all bookmarks for a specific user"""

    user = model.User.query.filter_by(username=username).first_or_404()

    if current_user.is_authenticated and user.id == current_user.id:
        include_private = True
    else:
        include_private = False

    results = model.Bookmark.\
              by_user(user.id, include_private=include_private).\
              paginate(page, app.config['PER_PAGE'])

    try:
        # the tagcloud() method is fragily; at the moment the best fix
        # is to catch the 0 division exception... :(
        tag_cloud = model.Tag.tagcloud(user_id=user.id)
    except ZeroDivisionError:
        tag_cloud = []

    return render_template('user_bookmarks.html', bookmarks=results,
                           for_user=user, tag_cloud=tag_cloud)


@app.route('/post', methods=['GET', 'POST'])
@login_required
def post_bookmark():
    """Posts a new bookmark (with a popup window)"""

    url = request.args.get('url', '')
    title = request.args.get('title', '')
    notes = request.args.get('notes', '')

    form = forms.BookmarkForm(request.form, url=url, title=title, notes=notes)
    if form.validate_on_submit():
        bookmark = form.create_bookmark(current_user)
        db.Session.add(bookmark)
        db.Session.commit()
        db.Session.refresh(bookmark)
        return redirect(url_for('close_popup'))

    return render_template('post_popup.html', form=form)


@app.route('/add', methods=['GET', 'POST'])
@login_required
def add():
    """Posts a new bookmark from the main UI"""

    url = request.args.get('url', '')
    title = request.args.get('title', '')

    form = forms.BookmarkForm(request.form, url=url, title=title)

    if form.validate_on_submit():
        bookmark = form.create_bookmark(current_user)
        db.Session.add(bookmark)
        db.Session.commit()
        db.Session.refresh(bookmark)

        flash(gettext("Bookmark added!"), "success")
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
        flash(gettext("Bookmark modified"), 'success')

        db.Session.refresh(bookmark)
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
        db.Session.delete(bookmark)
        db.Session.commit()

        flash(gettext("Bookmark deleted"), 'success')
        return form.redirect('index')

    return render_template('delete_bookmark.html', form=form, bookmark=bookmark)


@app.route('/bookmark/rename_tag', methods=['GET', 'POST'])
def rename_tag():
    form = forms.RenameTagForm()

    if form.validate_on_submit():
        old_name = form.old_name.data
        new_name = form.new_name.data

        assert old_name != new_name

        old_tag = model.Tag.query.filter_by(name=old_name).first()
        if old_tag is None:
            abort(404)

        new_tag = model.Tag.get_or_create(new_name)
        assert new_tag is not None

        query = model.Bookmark.by_tags([old_name])
        query = query.filter(model.Bookmark.user_id == current_user.id)

        for bookmark in query:
            bookmark.tags.remove(old_tag)
            bookmark.tags.append(new_tag)

        db.Session.commit()

        flash(gettext("Tag renamed successfully"), "success")
        return redirect(url_for('rename_tag'))

    return render_template('rename_tag.html', form=form)


@app.route('/bookmark/<int:bookmark_id>')
def single_bookmark(bookmark_id):
    bookmark = model.Bookmark.query.get_or_404(bookmark_id)

    if bookmark.private and bookmark.user.id != current_user.id:
        abort(404)

    return render_template('single.html', bookmark=bookmark)


@app.route('/search')
def simple_search():
    """Performs a simple search from the form on the navigation bar"""
    if 'query' not in request.args:
        abort(400)

    form = forms.SimpleSearchForm(request.args)

    # Limit search to current_user's bookmarks if 'personal' query arg
    # was specified
    if 'personal' in request.args:
        user_id = current_user.id
    elif 'user' in request.args:
        try:
            user_id = int(request.args.get('user'))
        except ValueError:
            abort(400)
    else:
        user_id = None

    if form.validate_on_submit:
        page = helpers.validate_page(form.page.data)

        # build a list of tags to be included and excluded from the query
        in_tags = []
        ex_tags = []
        for tag_name in form.query.data:
            # The leading '-' must be stripped from the excluded tag names!
            if tag_name.startswith('-'):
                ex_tags.append(tag_name[1:])
            else:
                in_tags.append(tag_name)

        results = []
        related = []
        if in_tags:
            results = model.Bookmark.by_tags(in_tags, ex_tags, user_id=user_id).\
                      paginate(page, app.config['PER_PAGE'])
            if app.config['ENABLE_RELATED_TAGS']:
                related = model.Tag.get_related(in_tags)

        return render_template('tag_results.html', bookmarks=results,
                               related=related)
    return redirect(url_for('index'))


@app.route('/followed', defaults={'page': 1})
@app.route('/followed/<int:page>')
def followed(page):
    bookmarks = model.Bookmark.by_followed().\
                paginate(page, app.config['PER_PAGE'])

    return render_template('followed.html', bookmarks=bookmarks)


@app.route('/feed/recent')
def feed_recent():
    feed = AtomFeed('QStode', feed_url=request.url,
                    url=request.url_root,
                    subtitle='Recent bookmarks')

    bookmarks = model.Bookmark.get_latest().\
                limit(app.config['FEED_NUM_ENTRIES']).all()

    for bookmark in bookmarks:
        item_id = urljoin(request.url_root,
                          url_for('single_bookmark', bookmark_id=bookmark.id))

        feed.add(title=bookmark.title,
                 title_type='text',
                 content=str(bookmark.notes),
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
    filename = 'qstode-backup-%s.html' % format_datetime(today, 'dd-MM-yyyy')

    resp = make_response(render_template('_export.html', bookmarks=bookmarks,
                                         today=today))
    resp.headers['Content-Type'] = 'application/octet-stream'
    resp.headers['Cache-Control'] = 'no-cache'
    resp.headers['Content-Disposition'] = 'attachment;filename=' + filename
    return resp
