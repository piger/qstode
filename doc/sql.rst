The SQL in QStode
=================

QStode has a pretty simple database schema where the most complicate thing is the tag system.

Complex queries
---------------

"Related tags" SQL query
''''''''''''''''''''''''

This query is a bit complicate because it involves a couple of JOIN statements and the use of
a many-to-many relation.

.. note:: This comes from StackOverflow: http://stackoverflow.com/questions/4483357/join-instead-of-subquery-for-related-tags

This is the code that we would like to express in SQLAlchemy:

.. code-block:: sql

  --- this query selects the ID for tag "games", which is '2'
  SELECT tags.id, tags.name FROM tags WHERE tags.name == "games";

  --- this query gets the related tags for the tag "games" (ID: 2)
  SELECT ta.id, ta.name, count(*) AS tot
  FROM bookmark_tags t2
  JOIN tags ta ON t2.tag_id=ta.id
  WHERE t2.bookmark_id IN (
    SELECT bookmark_id
    FROM bookmark_tags t1
    WHERE t1.tag_id IN (2)
    GROUP BY t1.bookmark_id
    HAVING COUNT(t1.tag_id) = 1
  ) AND ta.id NOT IN (2)
  GROUP BY ta.id
  ORDER BY tot DESC;

This is what we can achive with Python code and SQLAlchemy:

.. code-block:: sql

  SELECT tags.id AS tags_id, tags.name AS tags_name, count(?) AS tot
  FROM bookmark_tags JOIN tags ON bookmark_tags.tag_id = tags.id
  WHERE bookmark_tags.bookmark_id IN (SELECT bookmark_tags.bookmark_id
  FROM bookmark_tags
  WHERE bookmark_tags.tag_id IN (?) GROUP BY bookmark_tags.bookmark_id
  HAVING count(bookmark_tags.tag_id) = ?) AND tags.id NOT IN (?) GROUP BY tags.id ORDER BY tot desc

and it looks good :)
