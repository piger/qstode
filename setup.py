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
        'Babel==2.1.1',
        'Flask==0.10.1',
        'Flask-Babel==0.9',
        'Flask-Login==0.3.2',
        'Flask-WTF==0.12',
        'SQLAlchemy==1.0.10',
        'WTForms==2.1',
        'alembic==0.8.4',
        'MySQL-Python>=1.2.4',
        'iso8601==0.1.11',
        'pytz',
    ],
    setup_requires=[],
    zip_safe=False,
    include_package_data=True,
    packages=find_packages(),
    entry_points={
        "console_scripts": [
            "qstode = qstode.main:main",
            "qstode-scuttle-export = qstode.cli.scuttle_exporter:main",
        ],
    },
)
