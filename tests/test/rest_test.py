#!/usr/bin/python
# -*- coding: utf-8 -*-
"""File used to unit test the pacifica_cart."""
import os
from tempfile import mkdtemp
import requests
from cherrypy.test import helper
from pacifica.cartd.orm import Cart
from ..cart_db_setup_test import TestCartdBase


class TestRest(TestCartdBase, helper.CPWebCase):
    """Contain all the tests for the Cart Interface."""

    def test_cart_int_get(self):
        """Testing the cart interface get method w/o file_wrapper."""
        sample_cart = Cart()
        sample_cart.cart_uid = 123
        sample_cart.bundle_path = mkdtemp('', os.environ['VOLUME_PATH'])
        sample_cart.status = 'ready'
        sample_cart.save(force_insert=True)
        req = requests.get('{}/123'.format(self.url))
        self.assertEqual(req.status_code, 200)

    def test_invalid_cart_uid(self):
        """Testing the cart interface get against not valid cart uid."""
        req = requests.get('{}/123'.format(self.url))
        self.assertEqual(req.status_code, 404)
        self.assertFalse(req.json()['traceback'], 'traceback should be empty')

    def test_not_valid_cart(self):
        """Testing the cart interface get against not ready cart."""
        sample_cart = Cart()
        sample_cart.cart_uid = 123
        sample_cart.status = 'ready'
        sample_cart.save(force_insert=True)
        req = requests.get('{}/123'.format(self.url))
        self.assertEqual(req.status_code, 404)

    def test_not_ready_cart(self):
        """Testing the cart interface get against not ready cart."""
        sample_cart = Cart()
        sample_cart.cart_uid = 123
        sample_cart.bundle_path = mkdtemp('', os.environ['VOLUME_PATH'])
        sample_cart.save(force_insert=True)
        req = requests.head('{}/123'.format(self.url))
        self.assertEqual(req.status_code, 204)
        req = requests.get('{}/123'.format(self.url))
        self.assertEqual(req.status_code, 202)
        self.assertEqual(
            req.text,
            'The cart is not ready for download.',
            'the right text came out.'
        )

    def test_get_no_uid(self):
        """Testing the cart interface get."""
        req = requests.get('{}/'.format(self.url))
        self.assertEqual(req.status_code, 200)
        self.assertEqual(req.json()['message'], 'Pacifica Cartd Interface Up and Running')

    def test_status_invalid_uid(self):
        """Testing the cart interface status."""
        req = requests.head('{}/'.format(self.url))
        self.assertEqual(req.status_code, 500)

    def test_cart_int_delete(self):
        """Testing the cart interface delete."""
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
        req = requests.delete('{}/123'.format(self.url))
        self.assertEqual(req.status_code, 404)
