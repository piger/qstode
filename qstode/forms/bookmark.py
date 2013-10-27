# -*- coding: utf-8 -*-
"""
    qstode.forms.bookmark
    ~~~~~~~~~~~~~~~~~~~~~

    Bookmark related form definitions.

    :copyright: (c) 2012 by Daniel Kertesz
    :license: BSD, see LICENSE for more details.
"""
from flask_wtf import Form
from flask_wtf.html5 import URLField
from wtforms import (TextField, validators, ValidationError, Field,
                     BooleanField, TextAreaField, HiddenField,
                     SelectField, SubmitField)
from wtforms.widgets import TextInput
from flask_babel import lazy_gettext as _
from qstode.model.bookmark import Tag, Bookmark
from .misc import RedirectForm


class TagListField(Field):
    """A TextField suitable for comma separated words

    By default each word is stripped from extra whitespaces and duplicates
    are deleted.
    """

    widget = TextInput()

    def __init__(self, label='', validators=None, remove_duplicates=True,
                 **kwargs):
        super(TagListField, self).__init__(label, validators, **kwargs)
        self.remove_duplicates = remove_duplicates

    def _value(self):
        if self.data:
            return u', '.join(self.data)
        else:
            return u''

    def process_formdata(self, valuelist):
        if valuelist:
            self.data = [x.strip() for x in valuelist[0].split(',')]
        else:
            self.data = []

        if self.remove_duplicates:
            self.data = list(self._remove_duplicates(self.data))

    @classmethod
    def _remove_duplicates(cls, seq):
        d = {u'': True}

        for item in seq:
            if item.lower() not in d:
                d[item.lower()] = True
                yield item

class SimpleSearchForm(Form):
    query = TagListField(_(u'Search tags'),
                         [validators.Required(),
                          validators.Length(1,50)])
    page = HiddenField()

class AdvancedSearchForm(Form):
    # XXX: the name of this field currently cannot be "query" otherwise
    # it will conflicts with the global SimpleSearchForm
    q = TextField(_(u"Search query"), [validators.Required()])

class TypeaheadTextInput(TextInput):
    """A TextInput with javascript 'typeahead' support"""

    def __call__(self, field, **kwargs):
        kwargs['data-provide'] = u'typeahead'
        return super(TypeaheadTextInput, self).__call__(field, **kwargs)


class BookmarkForm(RedirectForm):
    """Form used to post new bookmarks"""

    title = TextField(_(u'Title'), [validators.Required()])
    url = URLField(_(u'URL'), [validators.URL()])
    private = BooleanField(_(u'Private'), default=False)
    tags = TagListField(_(u'Tag'),
                        [validators.Required(),
                         validators.Length(1,50)])
    notes = TextAreaField(_(u'Note'))

    def create_bookmark(self, user):
        data = {
            'title': self.title.data,
            'url': self.url.data,
            'private': self.private.data,
            'tags': list(self.tags.data),
            'notes': self.notes.data or u"",
            'user': user,
        }
        bookmark = Bookmark.create(data)
        return bookmark

    @classmethod
    def from_bookmark(cls, bookmark, data=None):
        form = cls(data,
                   url=bookmark.href,
                   title=bookmark.title,
                   private=bookmark.private,
                   notes=bookmark.notes,
                   tags=[t.name for t in bookmark.tags])
        return form


class TagSelectionForm(Form):
    tag = SelectField(_(u"Tag"), coerce=int)


class RenameTagForm(Form):
    to_name = TextField(_(u"Name"),
                        [validators.Required(),
                                  validators.Length(1, 30)])
    submit = SubmitField(_(u"Rename"))

    def validate_to_name(form, field):
        if Tag.query.filter_by(name=field.data).first():
            raise ValidationError(_(u"Tag already exists"))
