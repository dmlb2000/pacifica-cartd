#!/usr/bin/python
# -*- coding: utf-8 -*-
"""This tests some of the cart orm class."""
import os
import unittest
import mock
from peewee import OperationalError
from pacifica.cartd.__main__ import dbsync
from pacifica.cartd.orm import Cart, File, OrmSync
# pylint: disable=import-error
from cart_db_setup_test import cart_dbsetup_gen
# pylint: enable=import-error


class TestOrm(cart_dbsetup_gen(unittest.TestCase)):
    """Contains the cart orm tests."""

    def test_cart_orm_db_setup(self):
        """Call database_setup."""
        dbsync('blah')
        self.assertTrue(Cart.table_exists())
        self.assertTrue(File.table_exists())

    @mock.patch.object(Cart, 'database_connect')
    @mock.patch.object(File, 'database_connect')
    def test_cart_orm_db_setup_error(self, mock_cart_dbcon, mock_file_dbcon):
        """Call database_setup."""
        mock_cart_dbcon.side_effect = OperationalError('Failing')
        mock_file_dbcon.side_effect = OperationalError('Failing')
        hit_exception = False
        os.environ['DATABASE_CONNECT_ATTEMPTS'] = '3'
        try:
            OrmSync.dbconn_blocking()
        except OperationalError:
            hit_exception = True
        self.assertTrue(hit_exception)
        del os.environ['DATABASE_CONNECT_ATTEMPTS']
