#!/usr/bin/python
# -*- coding: utf-8 -*-
"""This tests some of the cart orm class."""
import unittest
import mock
from peewee import OperationalError
from cart.cart_orm import database_setup, Cart, File
from cart.test.cart_db_setup import cart_dbsetup_gen


class TestCartOrm(cart_dbsetup_gen(unittest.TestCase)):
    """Contains the cart orm tests."""

    def test_cart_orm_db_setup(self):
        """Call database_setup."""
        database_setup(8)
        self.assertTrue(Cart.table_exists())
        self.assertTrue(File.table_exists())

    @mock.patch.object(Cart, 'database_connect')
    @mock.patch.object(File, 'database_connect')
    def test_cart_orm_db_setup_error(self, mock_cart_dbcon, mock_file_dbcon):
        """Call database_setup."""
        mock_cart_dbcon.side_effect = OperationalError('Failing')
        mock_file_dbcon.side_effect = OperationalError('Failing')
        hit_exception = False
        try:
            database_setup(8)
        except OperationalError:
            hit_exception = True
        self.assertTrue(hit_exception)
