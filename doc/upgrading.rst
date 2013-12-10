Upgrading to Newer Releases
===========================

.. _upgrading-to-0120:

Version 0.1.20
--------------

The database schema was mercilessly altered; I suggest to backup
(somehow) to a json file before upgrading QStode.

.. _upgrading-to-0117:

Version 0.1.17
--------------

Apply the included alembic migration with: ::

  alembic upgrade head

Be sure to first create or update `alembic.ini` and make sure it can
connect to your database.
