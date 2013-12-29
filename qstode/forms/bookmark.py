# -*- coding: utf-8 -*-
"""
    qstode.forms.bookmark
    ~~~~~~~~~~~~~~~~~~~~~

    Bookmark related form definitions.

    :copyright: (c) 2012 by Daniel Kertesz
    :license: BSD, see LICENSE for more details.
"""
import re
from flask_wtf import Form
from flask_wtf.html5 import URLField
from wtforms import (TextField, ValidationError, Field,
                     BooleanField, TextAreaField, HiddenField,
                     SelectField, SubmitField)
from wtforms.validators import DataRequired, Length, URL, Regexp
from wtforms.widgets import TextInput
from flask_babel import lazy_gettext as _
from qstode.model.bookmark import Tag, Bookmark
from .misc import RedirectForm
from .validators import ItemsLength, ListLength, ListRegexp


# Validators for length of each tag
TAG_MIN = 1
TAG_MAX = 35

# Validators for length of tag list
TAGLIST_MIN = 1
TAGLIST_MAX = 50

# Tag names must be validated by this regex
_tag_re = re.compile(r'^\w[\w!?.,$-_]*$', re.U)

# Tag names in a search form must be validated by this regex, which allows
# a '-' in front of the tag names to indicate tags to be excluded from the
# search
_tag_search_re = re.compile(r'^[\w-][\w!?.,$-_]*$', re.U)


class TagListField(Field):
    """A TextField suitable for comma separated words

    By default each word is stripped from extra whitespaces and duplicates
    are deleted.
    """

    widget = TextInput()

    def __init__(self, label='', _validators=None, remove_duplicates=True,
                 **kwargs):
        super(TagListField, self).__init__(label, _validators, **kwargs)
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

        # remove empty values
        self.data = [x for x in self.data if x]

        if self.remove_duplicates:
            self.data = list(self._remove_duplicates(self.data))

    @classmethod
    def _remove_duplicates(cls, seq):
        """Remove duplicates in a case insensitive, but case preserving manner"""

        d = {}
        for item in seq:
            if item.lower() not in d:
                d[item.lower()] = True
                yield item


class SimpleSearchForm(Form):
    query = TagListField(_(u'Search tags'), [
        DataRequired(),
        ItemsLength(TAG_MIN, TAG_MAX),
        ListLength(TAGLIST_MIN, TAGLIST_MAX),
        ListRegexp(_tag_search_re),
    ])
    page = HiddenField()


class AdvancedSearchForm(Form):
    # XXX: the name of this field currently cannot be "query" otherwise
    # it will conflicts with the global SimpleSearchForm
    q = TextField(_(u"Search query"), [DataRequired()])


class TypeaheadTextInput(TextInput):
    """A TextInput with javascript 'typeahead' support"""

    def __call__(self, field, **kwargs):
        kwargs['data-provide'] = u'typeahead'
        return super(TypeaheadTextInput, self).__call__(field, **kwargs)


class BookmarkForm(RedirectForm):
    """Form used to post new bookmarks"""

    title = TextField(_(u'Title'), [DataRequired()])
    url = URLField(_(u'URL'), [DataRequired(), URL()])
    private = BooleanField(_(u'Private'), default=False)
    tags = TagListField(_(u'Tag'), [
        DataRequired(),
        ItemsLength(TAG_MIN, TAG_MAX),
        ListLength(TAGLIST_MIN, TAGLIST_MAX),
        ListRegexp(_tag_re),
    ])
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
    old_name = TextField(_("Tag name"), [
        DataRequired(),
        Length(TAG_MIN, TAG_MAX),
    ])
    new_name = TextField(_("New tag name"), [
        DataRequired(),
        Length(TAG_MIN, TAG_MAX),
    ])
