#!/usr/bin/env python3

from distutils.core import setup

setup(name='pyripedb',
    version='0.1',
    description='Python library to access RIPE.net RESTful API',
    author='Jiri Lunacek',
    author_email='jiri.lunacek@wygroup.io',
    packages = ['ripedb', 'ripedb.objects'],
)