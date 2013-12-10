# QStode

QStode is a web application that allows registered users to store bookmarks
(like the goold old del.icio.us) categorized by tags.

At the moment social functions (for example the subscription to other users
bookmark feed) are missing.

## Project status

QStode is mostly usable even if it still lacks some features and many
things could be improved.

Things to note:

- the search engine feature is still experimental mostly because it
  should really use a task queue (i.e. Celery) to handle all the write
  operations on the index; at the moment I'm using Whoosh
  `AsyncWriter` that relies on threads and is not suitable for high
  work loads.

- the included SQL query used to get *related tags* must not be used
  as it's buggy and will cause a very high load on your database.

- a MySQL database is suggested; PostgreSQL support is experimental/incomplete.

## Requirements

- a recent Python interpreter; I'm using 2.7.x as the supported Python version
- a WSGI server: gunicorn, uwsgi, etc.
- a web server with reverse proxy support

The suggested setup involves the use of a *virtual environmen* created with
`virtualenv`.

## Installation

Check out the `doc` directory.

## Author(s)

QStode is written and maintened by Daniel Kertesz <daniel@spatof.org>.

## License

- all (python, js) code is BSD licensed, see LICENSE file.
- all HTML and CSS code is licensed under cc-by-nc, see:
  http://creativecommons.org/licenses/by-nc/3.0/
