Database
========

Notes and Miscellaneous Informations
------------------------------------

With alembic a migration that involve dropping a column with a
constraints must be handled carefully. First you must find out the
name of the constraint running a command like:

.. code-block:: sql

  SHOW CREATE TABLE <tablename>;

For example the constraint name is `bookmarks_ibfk_3`, so you can now
create the alembic operation that will first drop the contraint and
then the column and the table:

.. code-block:: python

   def upgrade():
       op.drop_constraint('bookmarks_ibfk_3', 'bookmarks', 'foreignkey')
       op.drop_column("bookmarks", "category_id")
       op.drop_table("categories")
