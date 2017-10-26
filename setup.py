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
    version="0.2.1",
    description="A web application serving as a tag based archive of links",
    author="Daniel Kertesz",
    author_email="daniel@spatof.org",
    url="https://github.com/piger/qstode",
    license="BSD",
    long_description=__doc__,
    install_requires=[
        'Babel==2.5.1',
        'Flask==0.12.2',
        'Flask-Babel==0.11.2',
        'Flask-Login==0.4',
        'Flask-WTF==0.14.2',
        'SQLAlchemy==1.1.14',
        'WTForms==2.1',
        'alembic==0.8.4',
        'MySQL-Python>=1.2.4',
        'iso8601==0.1.12',
        'pytz',
    ],
    setup_requires=[],
    zip_safe=False,
    include_package_data=True,
    packages=find_packages(),
    entry_points="""
    [console_scripts]
    qstode-scuttle-export = qstode.cli.scuttle_exporter:main
    """,
)
