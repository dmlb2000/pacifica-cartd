#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Setup and install the cart."""
from os import path
from setuptools import setup, find_packages


setup(
    name='pacifica-cartd',
    use_scm_version=True,
    setup_requires=['setuptools_scm'],
    description='Pacifica Cartd',
    url='https://github.com/pacifica/pacifica-cartd/',
    long_description=open(path.join(
        path.abspath(path.dirname(__file__)),
        'README.md')).read(),
    long_description_content_type='text/markdown',
    author='David Brown',
    author_email='dmlb2000@gmail.com',
    packages=find_packages(include=['pacifica.*']),
    namespace_packages=['pacifica'],
    entry_points={
        'console_scripts': [
            'pacifica-cartd=pacifica.cartd.__main__:main',
            'pacifica-cartd-cmd=pacifica.cartd.__main__:cmd'
        ]
    },
    install_requires=[
        'celery',
        'cherrypy',
        'jsonschema',
        'pacifica-namespace',
        'peewee>2',
        'psutil',
        'pyyaml',
        'requests',
        'setuptools',
        'tqdm',
    ]
)
