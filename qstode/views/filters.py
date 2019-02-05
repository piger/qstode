"""
    qstode.views.filters
    ~~~~~~~~~~~~~~~~~~~~

    Jinja2 template filters.

    :copyright: (c) 2012 by Daniel Kertesz
    :license: BSD, see LICENSE for more details.
"""
import os
import re
import urllib.request
import urllib.error
import urllib.parse
import calendar
from datetime import datetime
from flask import request, url_for
from flask_babel import to_user_timezone, lazy_gettext as _
from qstode.app import app


domain_re = re.compile(r"https?://((?:[^\/]+|$))")


@app.template_filter("get_domain")
def get_domain(s):
    """Extracts the hostname from a URL"""

    match = domain_re.search(s)
    if match:
        return match.group(1)
    else:
        return ""


@app.template_filter("urlencode")
def tf_urlencode(s):
    """Returns the URL encoded version of a string"""
    return urllib.parse.quote(s.encode("utf-8"))


def url_for_other_page(page):
    """Get the URL for "other page" for Pagination menu"""

    args = request.view_args.copy()
    args["page"] = page
    args.update(request.args)
    return url_for(request.endpoint, **args)


app.jinja_env.globals["url_for_other_page"] = url_for_other_page


@app.template_filter()
def timesince(dt, default=None):
    """Convert a timestamp to a textual string describing "how much time ago".

    The parameter `dt` is a :class:`datetime.datetime` instance without
    timezone info (e.g. `tzinfo=None`).

    Original author: Dan Jacob
    URL: http://flask.pocoo.org/snippets/33/
    License: Public Domain
    """

    if default is None:
        default = _("now")

    user_dt = to_user_timezone(dt)
    now_dt = to_user_timezone(datetime.utcnow())

    diff = now_dt - user_dt

    periods = (
        (diff.days // 365, _("year"), _("years")),
        (diff.days // 30, _("month"), _("months")),
        (diff.days // 7, _("week"), _("weeks")),
        (diff.days, _("day"), _("days")),
        (diff.seconds // 3600, _("hour"), _("hours")),
        (diff.seconds // 60, _("minute"), _("minutes")),
        (diff.seconds, _("second"), _("seconds")),
    )

    for period, singular, plural in periods:
        if period:
            if period == 1:
                timestr = singular
            else:
                timestr = plural
            return _("%(num)s %(time)s ago", num=period, time=timestr)

    return default


@app.context_processor
def versioned_url_processor():
    """Wraps `url_for()` and is specific to static files; appends a 'v'
    parameter to the URL containing the timestamp of the requested file.
    This is useful to avoid caching of css and javascript files.
    """

    def versioned_url(filename):
        static_filename = os.path.join(app.static_folder, filename)
        modtime = os.path.getmtime(static_filename)
        static_url = url_for("static", filename=filename)
        return "%s?v=%d" % (static_url, modtime)

    return dict(versioned_url=versioned_url)


@app.context_processor
def active_if_processor():
    def active_if(endpoint):
        if request.endpoint == endpoint:
            return "active"
        return ""

    return dict(active_if=active_if)


@app.template_filter()
def ts_to_unix(t):
    """Convert a datetime object to an integer representing the current
    UNIX time."""
    return calendar.timegm(t.utctimetuple())
