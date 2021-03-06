"""
    qstode.forms.bookmark
    ~~~~~~~~~~~~~~~~~~~~~

    Bookmark related form definitions.

    :copyright: (c) 2012 by Daniel Kertesz
    :license: BSD, see LICENSE for more details.
"""
import re
from flask_wtf import FlaskForm
from wtforms import StringField, Field, BooleanField, TextAreaField, HiddenField, SelectField
from wtforms.fields.html5 import URLField
from wtforms.validators import DataRequired, Length, URL, Optional
from wtforms.widgets import TextInput
from flask_babel import lazy_gettext as _
from ..model.bookmark import tag_name_re, TAG_MIN, TAG_MAX, NOTES_MAX, create_bookmark
from .misc import RedirectForm
from .validators import ItemsLength, ListLength, ListRegexp


# Validation for length of tag list
TAGLIST_MIN = 1
TAGLIST_MAX = 50

# Tag names in a search form must be validated by this regex, which allows
# a '-' in front of the tag names to indicate tags to be excluded from the
# search
_tag_search_re = re.compile(r"^[\w-][\w!?.,$-_]*$", re.U)


class TagListField(Field):
    """A StringField suitable for comma separated words

    By default each word is stripped from extra whitespaces and duplicates
    are deleted.
    """

    widget = TextInput()

    def __init__(self, label="", _validators=None, remove_duplicates=True, **kwargs):
        super(TagListField, self).__init__(label, _validators, **kwargs)
        self.remove_duplicates = remove_duplicates

    def _value(self):
        if self.data:
            return ", ".join(self.data)
        else:
            return ""

    def process_formdata(self, valuelist):
        if valuelist:
            self.data = [x.strip() for x in valuelist[0].split(",")]
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


class SimpleSearchForm(FlaskForm):
    query = TagListField(
        _("Search tags"),
        [
            DataRequired(),
            ItemsLength(TAG_MIN, TAG_MAX),
            ListLength(TAGLIST_MIN, TAGLIST_MAX),
            ListRegexp(_tag_search_re),
        ],
    )
    page = HiddenField()


class TypeaheadTextInput(TextInput):
    """A TextInput with javascript 'typeahead' support"""

    def __call__(self, field, **kwargs):
        kwargs["data-provide"] = "typeahead"
        return super(TypeaheadTextInput, self).__call__(field, **kwargs)


class BookmarkForm(RedirectForm):
    """Form used to post new bookmarks"""

    title = StringField(_("Title"), [DataRequired()])
    url = URLField(_("URL"), [DataRequired(), URL()])
    private = BooleanField(_("Private"), default=False)
    tags = TagListField(
        _("Tag"),
        [
            DataRequired(),
            ItemsLength(TAG_MIN, TAG_MAX),
            ListLength(TAGLIST_MIN, TAGLIST_MAX),
            ListRegexp(tag_name_re),
        ],
    )
    notes = TextAreaField(_("Note"), [Optional(), Length(0, NOTES_MAX)])

    def create_bookmark(self, user):
        bookmark = create_bookmark(
            self.url.data,
            self.title.data,
            self.notes.data or "",
            list(self.tags.data),
            private=self.private.data,
        )
        user.bookmarks.append(bookmark)
        return bookmark

    @classmethod
    def from_bookmark(cls, bookmark, data=None):
        form = cls(
            data,
            url=bookmark.href,
            title=bookmark.title,
            private=bookmark.private,
            notes=bookmark.notes,
            tags=[t.name for t in bookmark.tags],
        )
        return form


class TagSelectionForm(FlaskForm):
    tag = SelectField(_("Tag"), coerce=int)


class RenameTagForm(FlaskForm):
    old_name = StringField(_("Tag name"), [DataRequired(), Length(TAG_MIN, TAG_MAX)])
    new_name = StringField(_("New tag name"), [DataRequired(), Length(TAG_MIN, TAG_MAX)])
