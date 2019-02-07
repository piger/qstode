# QStode

QStode is a web application that allows registered users to store bookmarks
(like the good old del.icio.us) categorized by tags.

At the moment social functions (for example the subscription to other users
bookmark feed) are missing.

## Project status

QStode is mostly usable (read: it's **beta**) even if it still lacks
some features and many things could be improved.

Things to note:

- the search engine feature is still experimental mostly because it
  should really use a task queue (i.e. Celery) to handle all the write
  operations on the index; at the moment I'm using Whoosh
  `AsyncWriter` that relies on threads and is not suitable for high
  work loads.

- a MySQL database is suggested; PostgreSQL support is experimental/incomplete.

## Documentation

Documentation is available on [ReadTheDocs][rtd].

[rtd]: http://qstode.readthedocs.org/en/latest/index.html

## Requirements

- Python 2.6 or 2.7
- a WSGI server: gunicorn, uwsgi, etc.
- a web server with reverse proxy support

The suggested setup involves the use of a *virtual environment* created with
`virtualenv`.

NOTE: You can also run QStode with the built in http server, but it's not suitable for the open internet!

## Docker

A sample `docker-compose.yml` file is provided as a starting point to run your own instance in
development mode.

To start QStode run:

``` shell
docker-compose up --build
```

To setup the database and create the _admin_ user, run:

``` shell
docker-compose run qstode setup
```

To shutdown the containers run:

``` powershell
docker-compose down
```

Or run `docker-compose down -v` to also delete the MySQL data container.

## Author(s)

QStode is written and maintained by Daniel Kertesz <daniel@spatof.org>.

## License

- all (python, js) code is BSD licensed, see LICENSE file.
- all HTML and CSS code is licensed under cc-by-nc, see:
  http://creativecommons.org/licenses/by-nc/3.0/
