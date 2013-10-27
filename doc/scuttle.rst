Export data from Scuttle
########################

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
