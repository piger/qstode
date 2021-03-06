Exporting data from Scuttle
###########################

Utilities
=========

QStode includes two utilities to export bookmark data from the
database of a `Scuttle`_ installation; the code was only partially
tested, so use with caution and remember to backup your data first.

Exporting data from Scuttle
---------------------------

``qstode-scuttle-export`` is a Python script that exports data from
the database of a `Scuttle`_ installation to either a **JSON** file or
a HTML file.

Access to the database is configured in a funny way; you must write a
configuration file containing just one value::

  uri = <sqlalchemy URI>

For example::

  uri = mysql://my-user:s3cRet@localhost/qstode

Check out the ``SQLALCHEMY_DATABASE_URI`` parameter in the
:doc:`configuration` page for more informations about the URI format.

To run the export utility::

  $ qstode-scuttle-export -c config.txt

After the operation is completed you will find a file named
``scuttle-export.json`` in your current directory.

Importing data from a Scuttle JSON export file
----------------------------------------------

To import a **JSON** backup file in QStode you must run the following
command::

  $ qstode -c /etc/qstode/config.py scuttle-import <backup-filename.json>

You have to specify the path to the main configuration file of your
QStode installation.

Please note that if you are importing data to a fresh installation of
QStode you will have to run the ``setup`` command before running the
import commands::

  $ qstode -c /etc/qstode/config.py setup

What to do if you have utf-8 data in a latin1 database
======================================================

See details about character encoding of your database::

  show create database `dbname`;

It should say that the default character encoding is ``latin``; please
note that any column could have a different character encoding
associated.

Now export data ensuring that MySQL won't change the encoding::

  mysqldump --default-character-set=utf8 --opt -u `user` -p `dbname` \
		> db-latin1.sql

Replace (this sound silly, I know) ``latin1`` with ``utf8`` in your
SQL dump::

  replace "CHARSET latin1" "CHARSET utf8" \
		"SET NAMES latin1" "SET NAMES utf8" \
		< db-latin1.sql > db-utf8.sql

The :command:`replace` command is part of MySQL.

Now you can create a new database specifying ``utf8`` as the default
character set::

  mysql --default-character-set=utf8 -u root -p
  > create database `mydb` character set utf8 collate utf8_bin;

Note that ``collate utf8_bin`` is optional.

It could also be necessary to change the collation of some tables; for
example in scuttle we have the table ``sc_tags`` where a key is made by
the ``bookmark_id`` and the ``tag_id``, but with the default collation
we have 'e' == 'è'::

  mysql> SELECT 'e' = 'è' COLLATE utf8_general_ci;
  +------------------------------------+
  | 'e' = 'è' COLLATE utf8_general_ci  |
  +------------------------------------+
  |                                  1 |
  +------------------------------------+

To fix this you can edit the SQL dump and add ``COLLATE=utf8_bin`` to
the ``CREATE TABLE`` statement of the problematic table.


.. _Scuttle: http://sourceforge.net/projects/scuttle/

How to really export data from a scuttle database infested with latin1
======================================================================

First I did the `mysqldump` as instructed below, also doing the `replace` step. Please note that some MySQL
versions use `CHARSET=latin1` instead of `CHARSET latin1` so adjust your command line accordingly.

Then I imported the sql dump in a new utf8 database.

Then I did some expertiments::

  mysql> select bDescription from sc_bookmarks where bDescription like '%a sort of%';
  | bDescription
  | This article attempts to give a sort of â€˜orientation tourâ€™ for people whose previous programming background is in high (ish) level languages such as Java or Python, and who now find that they need or want to learn C.
  1 row in set (0.02 sec)

  mysql> select convert(cast(convert(bDescription using  latin1) as binary) using utf8)
      -> from sc_bookmarks where bDescription like '%a sort of%';
  | convert(cast(convert(bDescription using  latin1) as binary) using utf8)
  | This article attempts to give a sort of ‘orientation tour’ for people whose previous programming background is in high (ish) level languages such as Java or Python, and who now find that they need or want to learn C.      |
  1 row in set (0.02 sec)

To fix this I issued a couple of UPDATEs:

.. code-block:: sql
   UPDATE sc_bookmarks SET
   bDescription=convert(cast(convert(bDescription using latin1) as binary) using utf8),
   bTitle=convert(cast(convert(bTitle using latin1) as binary) using utf8)
   WHERE 1;

   ALTER TABLE sc_tags convert to character set utf8 collate utf8_bin;

   UPDATE sc_tags SET
   tag=convert(cast(convert(tag using latin1) as binary) using utf8)
   WHERE 1;

The `ALTER TABLE` is explained in the previous chapter.

Finally I was able to dump the scuttle database to a JSON file and import it in QStode :)


