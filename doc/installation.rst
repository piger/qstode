Installation
============

QStode is a Python web application and depends on some external
libraries which can be installed via `setuptools`; it will also need a
web server capable of running WSGI applications.

You will need Python 2.6 or higher to get started and you should make
sure to install `setuptools`_ with your favourite package manager.

virtualenv
----------

`virtualenv`_ is the best way to manage your installation of QStode;
if you don't know what `virtualenv`_ is be sure to check out the
website and learn why you should use it with your web applications
deployment.

If you are in a hurry all you need to know is that `virtualenv`_
allow you to keep a separate *Python environment* with specific
versions of libraries and packages.

Ubuntu font
-----------

The InK framework uses the `Ubuntu Font` which must be manually
downloaded and extracted into `qstode-src-x.y.z/qstode/static/font`.

QStode Installation
-------------------

You must create a configuration file which by default is located in
`/etc/qstode/web_config.py` and make sure you specify a valid database
URI.

Create the database tables and default **admin** user::

   qstode -c config.py setup

A test server can be run with: ::

   qstode -c config.py -D server

MySQL
'''''

QStode need to store data in a MySQL database with **UTF-8** character
encoding; an example database can be created running the following
commands: ::

  # mysql -u root -p
  mysql> create database qstode character set utf8 collate utf8_bin;
  mysql> create user 'qstode'@'localhost' identified by 'somepass';
  mysql> grant all privileges on qstode.* to 'qstode'@'localhost';
  mysql> flush privileges;


System-Wide Installation
''''''''''''''''''''''''

This kind of installation is unsupported at the moment, use at your
own risk!

Example Test Installation
'''''''''''''''''''''''''

Here we describe an example **test** installation within a virtualenv::

   mkdir -p /srv/www/qstode /etc/qstode
   cd /srv/www/qstode
   virtualenv env
   source env/bin/activate
   git clone http://git.spatof.org/qstode.git
   cd qstode
   python setup.py develop
   cp flask_config_sample.py /etc/qstode/web_config.py
   qstode -c /etc/qstode/web_config.py setup
   qstode -c /etc/qstode/web_config.py -D server

Now you have a test server running on http://127.0.0.1:5000

Deployment with uWSGI
'''''''''''''''''''''

A configuration file to run QStode with `uWSGI`_:

.. code-block:: ini

   [uwsgi]
   plugin = python
   virtualenv = /path/to/qsto.de/env
   module = qstode.main
   callable = run_wsgi
   stats = 127.0.0.1:9191
   env = APP_CONFIG=/etc/qstode/web_config.py
   threads = 4
   # fix a buffer size problem related to Flask-OpenID
   buffer-size = 10240

A sample configuration for nginx: ::

  upstream qstode_uwsgi {
	  server unix:/run/uwsgi/app/qstode/socket;
  }

  server {
	  listen 80;

	  server_name example.com;

	  root /srv/www/qstode/htdocs;

	  location /static/ {
		  root /path/to/qstode-src-x.y.z/qstode/;
		  expires 15d;
		  add_header Pragma public;
		  add_header Cache-Control "public, must-revalidate, proxy-revalidate";
	  }

	  location / {
		  try_files $uri $uri/ @proxy_to_app;
	  }

	  location @proxy_to_app {
		  uwsgi_pass qstode_uwsgi;
		  uwsgi_param APP_CONFIG /etc/qstode/web_config.py;
		  include uwsgi_params;
	  }
  }

Migration and Backup
''''''''''''''''''''

You can backup all your data to a *JSON* file by running: ::

   qstode-backup -c /path/to/config.py filename.json

You can also import an existing backup by running: ::

   qstode-importer -c /path/to/config.py filename.json

After an import you must also recreate the Whoosh index; at the moment
the best way is to delete the existing Whoosh directory and run: ::

   qstode-index -c /path/to/config.py


.. _setuptools: https://pypi.python.org/pypi/setuptools
.. _virtualenv: http://www.virtualenv.org/en/latest/
.. _uWSGI: https://github.com/unbit/uwsgi
.. _Ubuntu Font: http://font.ubuntu.com/
