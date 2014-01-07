# -*- coding: utf-8 -*-
"""
QStode
------

QStode is a web application serving as a tag based archive of internet links.
It's free software based on the excellent Flask microframework and SQLAlchemy.

`QStode <http://qsto.de>`_

"""
from setuptools import setup, find_packages


setup(
    name="qstode",
    version="0.2b1",
    description="A web application serving as a tag based archive of links",
    author="Daniel Kertesz",
    author_email="daniel@spatof.org",
    url="https://github.com/piger/qstode",
    license="BSD",
    long_description=__doc__,
    install_requires=[
        'argparse',
        'Babel',
        'Flask',
        'Flask-Babel',
        'Flask-Login',
        'Flask-WTF',
        'SQLAlchemy<0.9',
        'WTForms',
        'alembic',
        #'distribute==0.6.45',
        'MySQL-Python>=1.2.4',
        'iso8601',
        'pytz',
        'Whoosh',
        'redis',
    ],
    setup_requires=[],
    test_requires=['Flask-Testing', 'mock', 'nose'],
    zip_safe=False,
    include_package_data=True,
    packages=find_packages(),
    entry_points={
        "console_scripts": [
            "qstode = qstode.main:main",
            "qstode-indexer = qstode.search.server:main",
            "qstode-scuttle-export = qstode.cli.scuttle_exporter:main",
        ],
    },
)
