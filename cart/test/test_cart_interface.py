#!/usr/bin/python
# -*- coding: utf-8 -*-
"""File used to unit test the pacifica_cart."""
import os
import logging
from tempfile import mkstemp, mkdtemp
import cherrypy
from cherrypy.test import helper
from playhouse.test_utils import test_database
from peewee import SqliteDatabase
import requests
from cart.__main__ import error_page_default
from cart.cart_orm import Cart, File
from cart.cart_interface import CartRoot
from cart.celery import CART_APP

CART_APP.conf.CELERY_ALWAYS_EAGER = True


# there's a lot of testing with this class suckit pylint
# pylint: disable=too-many-public-methods
class TestCartInterface(helper.CPWebCase):
    """Contain all the tests for the Cart Interface."""

    PORT = 8081
    HOST = '127.0.0.1'
    url = 'http://{0}:{1}'.format(HOST, PORT)
    headers = {'content-type': 'application/json'}
    sqlite_db_path = mkstemp(suffix='.interface.sqlite3')[1]

    @staticmethod
    def setup_server():
        """Start all the services."""
        logger = logging.getLogger('urllib2')
        logger.setLevel(logging.DEBUG)
        logger.addHandler(logging.StreamHandler())
        os.environ['VOLUME_PATH'] = '{}{}'.format(mkdtemp(), os.path.sep)
        cherrypy.config.update({'error_page.default': error_page_default})
        cherrypy.config.update('server.conf')
        cherrypy.tree.mount(CartRoot(), '/', 'server.conf')

    def test_cart_int_get(self):
        """Testing the cart interface get method w/o file_wrapper."""
        with test_database(SqliteDatabase(self.sqlite_db_path), (Cart, File)):
            sample_cart = Cart()
            sample_cart.cart_uid = 123
            sample_cart.bundle_path = mkdtemp('', os.environ['VOLUME_PATH'])
            sample_cart.status = 'ready'
            sample_cart.save(force_insert=True)
            req = requests.get('{}/123'.format(self.url))
            self.assertEqual(req.status_code, 200)

    def test_invalid_cart_uid(self):
        """Testing the cart interface get against not valid cart uid."""
        with test_database(SqliteDatabase(self.sqlite_db_path), (Cart, File)):
            req = requests.get('{}/123'.format(self.url))
            self.assertEqual(req.status_code, 404)

    def test_not_valid_cart(self):
        """Testing the cart interface get against not ready cart."""
        with test_database(SqliteDatabase(self.sqlite_db_path), (Cart, File)):
            sample_cart = Cart()
            sample_cart.cart_uid = 123
            sample_cart.status = 'ready'
            sample_cart.save(force_insert=True)
            req = requests.get('{}/123'.format(self.url))
            self.assertEqual(req.status_code, 404)

    def test_not_ready_cart(self):
        """Testing the cart interface get against not ready cart."""
        with test_database(SqliteDatabase(self.sqlite_db_path), (Cart, File)):
            sample_cart = Cart()
            sample_cart.cart_uid = 123
            sample_cart.bundle_path = mkdtemp('', os.environ['VOLUME_PATH'])
            sample_cart.save(force_insert=True)
            req = requests.head('{}/123'.format(self.url))
            self.assertEqual(req.status_code, 204)
            req = requests.get('{}/123'.format(self.url))
            self.assertEqual(req.status_code, 202)
            self.assertEqual(
                req.text, 'The cart is not ready for download.', 'the right text came out.')

    def test_status_invalid_uid(self):
        """Testing the cart interface status."""
        with test_database(SqliteDatabase(self.sqlite_db_path), (Cart, File)):
            req = requests.head('{}/'.format(self.url))
            self.assertEqual(req.status_code, 500)

    def test_cart_int_delete(self):
        """Testing the cart interface delete."""
        with test_database(SqliteDatabase(self.sqlite_db_path), (Cart, File)):
            sample_cart = Cart()
            sample_cart.cart_uid = 123
            sample_cart.bundle_path = mkdtemp('', os.environ['VOLUME_PATH'])
            sample_cart.status = 'ready'
            sample_cart.save(force_insert=True)
            sample_cart.reload()
            req = requests.delete('{}/123'.format(self.url))
            self.assertEqual(req.status_code, 200)

    def test_delete_invalid_uid(self):
        """Testing the cart interface delete with invalid uid."""
        with test_database(SqliteDatabase(self.sqlite_db_path), (Cart, File)):
            req = requests.delete('{}/123'.format(self.url))
            self.assertEqual(req.status_code, 404)
