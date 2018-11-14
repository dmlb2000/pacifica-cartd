#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Setup and install the cart."""
try:  # pip version 9
    from pip.req import parse_requirements
except ImportError:
    from pip._internal.req import parse_requirements
from setuptools import setup, find_packages

# parse_requirements() returns generator of pip.req.InstallRequirement objects
INSTALL_REQS = parse_requirements('requirements.txt', session='hack')

setup(
    name='pacifica-cartd',
    use_scm_version=True,
    setup_requires=['setuptools_scm'],
    description='Pacifica Cartd',
    author='David Brown',
    author_email='dmlb2000@gmail.com',
    packages=find_packages(),
    namespace_packages=['pacifica'],
    entry_points={
        'console_scripts': [
            'pacifica-cartd=pacifica.cartd.__main__:main',
            'pacifica-cartd-cmd=pacifica.cartd.__main__:cmd'
        ]
    },
    install_requires=[str(ir.req) for ir in INSTALL_REQS]
)
