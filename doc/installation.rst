Installation
============

QStode is a Python web application and depends on some external
libraries which can be installed via `setuptools`_; it will also need a
web server capable of running WSGI applications.

Requirements
------------

* Python >= 2.6
* MySQL 5.x database
* python-setuptools
* python-mysqldb (also packaged as **MySQL-Python**)
* WSGI server (e.g gunicorn)
* Web server
* one writable directory

You *may* also need:

* git
* python-virtualenv
* Redis database
* c/c++ compiler

Ubuntu example::

  $ sudo apt-get install python-setuptools python-dev python-virtualenv \
      git mysql-server gunicorn build-essential
  
Getting the sources
-------------------

You can download a tarball of the latest release from the `releases`_ page
on `GitHub`_, or you can *clone* the repository with git::

  $ cd /usr/local/src
  $ git clone https://github.com/piger/qstode.git

Installing Python packages
--------------------------

`virtualenv`_ is the best way to manage your installation of QStode;
if you don't know what `virtualenv`_ is be sure to check out the
website and learn why you should use it with your web applications
deployment.

Create a virtualenv::

  $ virtualenv /srv/qstode/env

Install QStode with setuptools::

  $ source /srv/qstode/env/bin/activate
  $ cd /usr/local/src/qstode
  $ python setup.py install

Database setup
--------------

QStode need to store data in a MySQL database with **UTF-8** character
encoding; an example database can be created running the following
SQL commands: :

.. code-block:: mysql

  mysql> create database qstode character set utf8 collate utf8_bin;
  mysql> create user 'qstode'@'localhost' identified by 'somepass';
  mysql> grant all privileges on qstode.* to 'qstode'@'localhost';
  mysql> flush privileges;

Configuration file
------------------

See :doc:`configuration` for details about the configuration file.

Initial setup
-------------

You must create a configuration file in a directory readable by the
WSGI server process, for example ``/etc/qstode/config.py``.

To create the database tables and the admin user (remember to activate
the virtualenv first!)::

  $ source /srv/qstode/env/bin/activate
  $ qstode -c /etc/qstode/config.py setup

You can test your installation by running a local server with the command::

  $ qstode -c /etc/qstode/config.py server

A **DEBUG** mode is also available::

  $ qstode -c /etc/qstode/config.py -D server

Deployment
----------

Deployment with uWSGI
'''''''''''''''''''''

A configuration file to run QStode with `uWSGI`_:

.. code-block:: ini

   [uwsgi]
   plugin = python
   virtualenv = /srv/qstode/env
   module = qstode.main
   callable = run_wsgi
   stats = 127.0.0.1:9191
   env = APP_CONFIG=/etc/qstode/config.py
   threads = 4

A sample configuration for nginx:

.. code-block:: nginx

  upstream qstode_uwsgi {
      server unix:/run/uwsgi/app/qstode/socket;
  }

  server {
      listen 80;

      server_name example.com;

      root /srv/qstode/htdocs;

      location /static/ {
          root /usr/local/src/qstode/qstode/;
          expires 15d;
          add_header Pragma public;
          add_header Cache-Control "public, must-revalidate, proxy-revalidate";
      }

      location / {
          try_files $uri $uri/ @proxy_to_app;
      }

      location @proxy_to_app {
          uwsgi_pass qstode_uwsgi;
          uwsgi_param APP_CONFIG /etc/qstode/config.py;
          include uwsgi_params;
      }
  }

Migration and Backup
--------------------

You can backup all your data to a *JSON* file by running the
``backup`` command::

   $ qstode -c /path/to/config.py backup filename.json

You can also import an existing backup by running the ``import`` command::

   $ qstode -c /path/to/config.py import filename.json

After an import you must also recreate the Whoosh index; at the moment
the best way is to delete any existing Whoosh directory and then index
again all your content, running the ``reindex`` command::

   $ qstode -c /path/to/config.py reindex


.. _setuptools: https://pypi.python.org/pypi/setuptools
.. _releases: https://github.com/piger/qstode/releases
.. _GitHub: https://github.com/piger/qstode
.. _virtualenv: http://www.virtualenv.org/en/latest/
.. _uWSGI: https://github.com/unbit/uwsgi
