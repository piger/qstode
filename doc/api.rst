API
###

JSON data format
================

A bookmark in QStode is serialized to a JSON dictionary; for example:

.. code-block:: json

   {
     "results": {
       "modified_on": "2012-06-08T11:14:18",
       "title": "A caldo: che cos\u2019\u00e8 questo golpe?\u00a0|\u00a0Giap",
       "url": "http://www.wumingfoundation.com/giap/?p=8016&cpage=1&utm_source=dlvr.it&utm_medium=twitter#comment-12257",
       "notes": "La \u201cstrategia della tensione\u201d \u00e8 sempre una strategia di controrivoluzione preventiva.\r\n",
       "tags": [
	     "attualita'",
	     "terrorismo",
	     "wu-ming"
       ],
       "id": 1,
       "private": false,
       "created_on": "2012-05-20T23:47:14"
     }
   }

The dictionary keys are:

id
    Internal ID of the bookmark.

title
    Title given to the bookmark by the owner.

url
    URL of the bookmarked item.

tags
    The list of tags assigned to the bookmark.

notes
    The optional notes field.

private
    Privacy status of the bookmark.

created_on
    Date and time of the bookmark creation.

modified_on
    Date and time of the last modification to the bookmark data.

.. note:: All timestamps are in UTC format!

API Endpoints
=============

.. http:get:: /api/bookmarks/

Get all Bookmarks, with pagination.

**Example request**:

.. sourcecode:: http

   GET /api/bookmarks/ HTTP/1.1
   Host: example.com
   Accept: application/json, text/javascript

**Example response**:

.. sourcecode:: http

   HTTP/1.1 200 OK
   Content-Type: text/javascript

   {
     "results": {
       "bookmarks": [
	 {
	   "modified_on": "2013-06-27T19:06:36",
	   "title": "Occupy Gezi",
	   "url": "http://occupygezi.neocities.org/",
	   "notes": " Timemap of the events in Turkey between June 5th and June 17th (2013) as seen here: gezipark.nadir.org.",
	   "tags": [
	     "gezi park",
	     "mappa",
	     "occupy",
	     "turkey"
	   ],
	   "id": 712,
	   "private": false,
	   "created_on": "2013-06-27T19:06:36"
	 },
     }
   }

:query sort: one of ``date``, ``user``
:query offset: offset number, default is 0
:statuscode 200: success
:statuscode 404: error

.. http:get:: /api/bookmarks/(int:bookmark_id)

Retrieve a single Bookmark by the given `bookmark_id`.

**Example request**:

.. sourcecode:: http

   GET /api/bookmarks/1 HTTP/1.1
   Host: example.com
   Accept: application/json, text/javascript

**Example response**:

.. sourcecode:: http

   HTTP/1.0 200 OK
   Content-Type: text/javascript

   {
     "results": {
       "modified_on": "2012-06-08T11:14:18",
       "title": "A caldo: che cos\u2019\u00e8 questo golpe?\u00a0|\u00a0Giap",
       "url": "http://www.wumingfoundation.com/giap/?p=8016&cpage=1&utm_source=dlvr.it&utm_medium=twitter#comment-12257",
       "notes": "La \u201cstrategia della tensione\u201d \u00e8 sempre una strategia di controrivoluzione preventiva.\r\n",
       "tags": [
		 "attualita'",
		 "terrorismo",
		 "wu-ming"
       ],
       "id": 1,
       "private": false,
       "created_on": "2012-05-20T23:47:14"
     }
   }

:statuscode 200: success
:statuscode 400: error processing the request
