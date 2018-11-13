#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Test cart database setup class."""
from peewee import SqliteDatabase
from pacifica.cartd.orm import Cart, File


def cart_dbsetup_gen(parent_cls):
    """Generate a class with parent and call super on setup for parent."""
    class CartDBSetup(parent_cls):
        """Contain all the tests for the Cart Interface."""

        @staticmethod
        def create_sample_cart(cart_uid='1', status='staging', bundle_path='/tmp/1/'):
            """Create a sample cart."""
            return Cart.create(
                cart_uid=cart_uid,
                status=status,
                bundle_path=bundle_path
            )

        @staticmethod
        def create_sample_file(test_cart, file_name='1.txt', bundle_path='/tmp/1/1.txt'):
            """Create a sample file in cart."""
            return File.create(
                cart=test_cart,
                file_name=file_name,
                bundle_path=bundle_path
            )

        # pylint: disable=invalid-name
        def setUp(self):
            """Setup the database with in memory sqlite."""
            self._db = SqliteDatabase('file:cachedb?mode=memory&cache=shared')
            for model in [Cart, File]:
                model.bind(self._db, bind_refs=False, bind_backrefs=False)
            self._db.connect()
            self._db.create_tables([Cart, File])

        def tearDown(self):
            """Tear down the database."""
            self._db.drop_tables([Cart, File])
            self._db.close()
            self._db = None
        # pylint: enable=invalid-name
    return CartDBSetup
