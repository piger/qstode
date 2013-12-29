# -*- coding: utf-8 -*-
"""
    qstode.views.admin
    ~~~~~~~~~~~~~~~~~~

    Administration related views.

    :copyright: (c) 2012 by Daniel Kertesz
    :license: BSD, see LICENSE for more details.
"""
from functools import wraps
from flask import request, render_template, abort, redirect, url_for, flash
from flask_login import current_user
from flask_babel import gettext
from qstode.app import app
from qstode import db
from ..model import User, Bookmark
from qstode import forms


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.is_authenticated() and current_user.admin is True:
            return f(*args, **kwargs)
        # abort with FORBIDDEN
        abort(403)
    return decorated_function


@app.route("/admin")
@admin_required
def admin_home():
    return render_template("admin/index.html")


@app.route('/admin/users', defaults={'page': 1})
@app.route('/admin/users/<int:page>')
@admin_required
def admin_users(page):
    users = User.query.paginate(page, app.config['PER_PAGE'])
    return render_template("admin/list_users.html", users=users)


@app.route('/admin/create_user', methods=['GET', 'POST'])
@admin_required
def admin_create_user():
    form = forms.CreateUserForm()

    if form.validate_on_submit():
        user = User(form.username.data,
                          form.email.data,
                          form.password.data,
                          admin=form.admin.data,
                          active=form.active.data)
        db.Session.add(user)
        db.Session.commit()

        flash(gettext(u"Successfully created user %(username)s", username=user.username), "success")
        return redirect(url_for("admin_users"))

    return render_template("admin/create_user.html", form=form)


@app.route('/admin/delete_user/<int:id>', methods=['GET', 'POST'])
@admin_required
def admin_delete_user(id):
    user = User.query.get_or_404(id)
    form = forms.DeleteUserForm(next=request.referrer, user_id=user.id)

    if form.validate_on_submit():
        username = user.username
        db.Session.delete(user)
        db.Session.commit()

        flash(gettext(u"User %(username)s deleted", username=username),
              "success")
        return form.redirect()

    return render_template("admin/delete_user.html", user=user, form=form)


@app.route('/admin/user/<int:id>', methods=['GET', 'POST'])
@admin_required
def admin_edit_user(id):
    user = User.query.get_or_404(id)

    # Create the required form, populating with data from the selected
    # user; update also the dynamic field `choices`.
    form = forms.EditUserForm(username=user.username,
                              email=user.email,
                              admin=user.admin,
                              active=user.active)

    if form.validate_on_submit():
        user.username = form.username.data
        user.active = form.active.data
        if form.password.data:
            user.set_password(form.password.data)
        user.admin = form.admin.data

        user.email = form.email.data
        db.Session.commit()

        flash(gettext(u"User %(user)s updated", user=user.username), "success")
        return redirect(url_for('admin_users'))

    return render_template("admin/edit_user.html", user=user, form=form)
