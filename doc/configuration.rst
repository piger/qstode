Configuration
#############

Configuration handling in QStode is inherited from `Flask`_, therefore
it's managed by a Python script used as a configuration file.

Configuration parameters
========================

The following configuration values have the same meaning they have in
`Flask`_ (default values between parenthesis):

DEBUG (``False``)
  Enable or disable debug mode.

SECRET_KEY
  The secret key used by cryptography functions; you can use a random
  string or generate one with Python::

	$ python -c 'import os; print "%r" % os.urandom(24)'

SQLALCHEMY_DATABASE_URI
  The URI containing the parameters for connecting to the database, in
  the format ``drivername://username:password@address[:port]/dbname``.

  Example: ``mysql://my-user:s3cRet@localhost/qstode``.

.. note:: To use any database other then SQLite you must install the
		  corresponding Python driver; for example to use a MySQL
		  database you must install the ``MySQL-Python`` package.
  
The following configuration values are specific to QStode:

PUBLIC_ACCESS (``True``)
  Enable anonymous access to all the public pages; if set to ``False``
  a valid user is required to browse the application.

USER_REGISTRATION_ENABLED (``True``)
  Allow anonymous users to register themselves.

ENABLE_RECAPTCHA (``True``)
  Enable use of Recaptcha service (see also: ``RECAPTCHA_PUBLIC_KEY``, etc.).

PER_PAGE (``10``)
  Specify how many bookmarks to show on each page.

FEED_NUM_ENTRIES (``15``)
  Specify how many bookmarks to list in the public RSS feed.

TAGLIST_ITEMS (``30``)
  Specify how many tags to show in the Popular Tags listing.

ENABLE_RELATED_TAGS (``True``)
  Enable functions to show related tags in the *search* views.

.. warning:: The ``related tag`` feature is currently half-broken when
			 using MySQL without InnoDB.

BABEL_DEFAULT_LOCALE (``en``)
  The default locale to use if no locale selector is registered.

BABEL_DEFAULT_TIMEZONE (``UTC``)
  The timezone to use for user facing dates.

EXTRA_TEMPLATES (``[]``)
  A optional **list** of directories containing Jinja2 templates that
  will override the built in templates.

  Example: ``EXTRA_TEMPLATES = [ "/srv/www/my_templates" ]``
  
WHOOSH_INDEX_PATH
  The directory used to store the search engine's files; must be
  writable by the user running QStode.

USE_GOOGLE_FAVICON (``True``)
  Enable or disable the use of Google services to display *favicons*
  for bookmarked sites.

.. note:: This feature can be disabled by paranoid users ;)

REDIS_HOST, REDIS_PORT, REDIS_DB, REDIS_PASSWORD
  Redis connection parameters.

Recaptcha
---------

RECAPTCHA_USE_SSL
  Enable/disable recaptcha through ssl.

RECAPTCHA_PUBLIC_KEY
  Recaptcha public key.

RECAPTCHA_PRIVATE_KEY
  Recaptcha private key.

.. _Flask: http://flask.pocoo.org/docs/config/
