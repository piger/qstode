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
from qstode import model
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

@app.route('/admin/users')
@admin_required
def admin_users():
    users = model.User.query.all()
    return render_template("admin/list_users.html", users=users)

@app.route('/admin/create_user', methods=['GET', 'POST'])
@admin_required
def admin_create_user():
    form = forms.AdminUserCreationForm()

    if form.validate_on_submit():
        user = model.User(form.username.data,
                          form.email.data,
                          form.password.data,
                          admin=form.admin.data)
        db.Session.add(user)
        db.Session.commit()

        flash(gettext(u"Successfully created user %(username)s", username=user.email), "success")
        return redirect(url_for("admin_users"))

    return render_template("admin/create_user.html", form=form)

@app.route('/admin/delete_user/<int:id>', methods=['GET', 'POST'])
@admin_required
def admin_delete_user(id):
    user = model.User.query.get_or_404(id)

    # What to do with existing bookmarks?
    # If we delete all we must also de-index them...
        
    return render_template("admin/delete_user.html", user=user)

@app.route('/admin/users/<int:id>', methods=['GET', 'POST'])
@admin_required
def admin_edit_user(id):
    user = model.User.query.get_or_404(id)

    # Create the required form, populating with data from the selected
    # user; update also the dynamic field `choices`.
    form = forms.AdminModifyUserForm(request.form,
                                     username=user.username,
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

        flash(gettext(u"User %(user)s updated", user=user.email), "success")
        return redirect(url_for('admin_users'))

    return render_template("admin/edit_user.html", user=user, form=form)
