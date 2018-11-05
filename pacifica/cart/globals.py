#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Used to load in all the carts environment variables.

Wrapped all in if statements so that they can be used in
unit test environment
"""
from os.path import expanduser, join
from os import getenv
import logging


CONFIG_FILE = getenv('CART_CONFIG', join(
    expanduser('~'), '.pacifica-cartd', 'config.ini'))
CHERRYPY_CONFIG = getenv('CART_CPCONFIG', join(
    expanduser('~'), '.pacifica-cartd', 'cpconfig.ini'))

# this is intended to be a specific config separate from other temporary files
VOLUME_PATH = getenv('VOLUME_PATH', '/tmp/')

# buffer used for least recently used delete
LRU_BUFFER_TIME = getenv('LRU_BUFFER_TIME', 0)

# database logging for query tracking
DATABASE_LOGGING = getenv('DATABASE_LOGGING', False)
if DATABASE_LOGGING:
    LOGGER = logging.getLogger('peewee')
    LOGGER.setLevel(logging.DEBUG)
    LOGGER.addHandler(logging.StreamHandler())

# Number of attempts to connect to database.  Default 3
DATABASE_CONNECT_ATTEMPTS = getenv('DATABASE_CONNECT_ATTEMPTS', 10)

# time between trying to reconnect to database.  Default 10 seconds
DATABASE_WAIT = getenv('DATABASE_WAIT', 20)
