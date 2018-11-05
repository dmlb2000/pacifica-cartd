#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Configuration reading and validation module."""
from os import getenv
try:
    from ConfigParser import SafeConfigParser
except ImportError:  # pragma: no cover python 2 vs 3 issue
    from configparser import SafeConfigParser
from pacifica.cart.globals import CONFIG_FILE


def get_config():
    """Return the ConfigParser object with defaults set."""
    configparser = SafeConfigParser()
    configparser.add_section('cart')
    configparser.set('cart', 'volume_path', getenv(
        'VOLUME_PATH', '/tmp/'))
    configparser.set('cart', 'lru_buffer_time', getenv(
        'LRU_BUFFER_TIME', '0'))
    configparser.add_section('database')
    configparser.set('database', 'peewee_url', getenv(
        'PEEWEE_URL', 'sqliteext:///db.sqlite3'))
    configparser.add_section('archiveinterface')
    configparser.set('archiveinterface', 'url', getenv(
        'ARCHIVE_INTERFACE_URL', 'http://127.0.0.1:8080/'))
    configparser.read(CONFIG_FILE)
    return configparser
