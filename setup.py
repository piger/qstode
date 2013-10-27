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
    version="0.1.18",
    description="A web application serving as a tag based archive of links",
    author="Daniel Kertesz",
    author_email="daniel@spatof.org",
    url="http://qsto.de",
    license="BSD",
    long_description=__doc__,
    install_requires=[
        'argparse',
        'Babel',
        'Flask',
        'Flask-Babel',
        'Flask-Login',
        'Flask-OpenID',
        'Flask-SQLAlchemy',
        'Flask-WTF',
        'SQLAlchemy<0.9',
        'WTForms',
        'alembic',
        #'distribute==0.6.45',
        #'MySQL-Python==1.2.4',
        'iso8601',
        #'mock==1.0.1',
        #'pytest==2.3.4',
        'pytz',
        'Whoosh',
    ],
    setup_requires=[],
    zip_safe=False,
    include_package_data=True,
    packages=find_packages(),
    entry_points={
        "console_scripts": [
            "qstode = qstode.main:main",
        ],
    },
)
