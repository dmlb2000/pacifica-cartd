#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Used to load in all the carts environment variables.

Wrapped all in if statements so that they can be used in
unit test environment
"""
from os.path import expanduser, join
from os import getenv


CONFIG_FILE = getenv('CARTD_CONFIG', join(
    expanduser('~'), '.pacifica-cartd', 'config.ini'))
CHERRYPY_CONFIG = getenv('CARTD_CPCONFIG', join(
    expanduser('~'), '.pacifica-cartd', 'cpconfig.ini'))
