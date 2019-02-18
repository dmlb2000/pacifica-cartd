#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Configuration reading and validation module."""
from os import getenv
import logging
try:
    from ConfigParser import SafeConfigParser
except ImportError:  # pragma: no cover python 2 vs 3 issue
    from configparser import ConfigParser as SafeConfigParser
from .globals import CONFIG_FILE


def get_config():
    """Return the ConfigParser object with defaults set."""
    configparser = SafeConfigParser()
    configparser.add_section('cartd')
    configparser.set('cartd', 'transfer_size', getenv(
        'TRANSFER_SIZE', '4 Mb'))
    configparser.set('cartd', 'volume_path', getenv(
        'VOLUME_PATH', '/tmp/'))
    configparser.set('cartd', 'lru_buffer_time', getenv(
        'LRU_BUFFER_TIME', '0'))
    configparser.set('cartd', 'bundle_task', getenv(
        'BUNDLE_TASK', 'off'))
    configparser.add_section('database')
    configparser.set('database', 'peewee_url', getenv(
        'PEEWEE_URL', 'sqliteext:///db.sqlite3'))
    configparser.set('database', 'debug_logging', getenv(
        'DATABASE_DEBUG_LOGGING', 'False'))
    configparser.set('database', 'connect_attempts', getenv(
        'DATABASE_CONNECT_ATTEMPTS', '10'))
    configparser.set('database', 'connect_wait', getenv(
        'DATABASE_CONNECT_WAIT', '20'))
    configparser.add_section('archiveinterface')
    configparser.set('archiveinterface', 'url', getenv(
        'ARCHIVE_INTERFACE_URL', 'http://127.0.0.1:8080/'))
    configparser.add_section('celery')
    configparser.set('celery', 'broker_url', getenv(
        'BROKER_URL', 'pyamqp://'))
    configparser.set('celery', 'backend_url', getenv(
        'BACKEND_URL', 'rpc://'))
    configparser.read(CONFIG_FILE)
    return configparser


if get_config().getboolean('database', 'debug_logging'):  # pragma: no cover used for debugging
    LOGGER = logging.getLogger('peewee')
    LOGGER.setLevel(logging.DEBUG)
    LOGGER.addHandler(logging.StreamHandler())
