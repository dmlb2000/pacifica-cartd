#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Cart Object Relational Model.

Using PeeWee to implement the ORM.
"""
# disable this for classes Cart, File and Meta (within Cart and File)
# pylint: disable=too-few-public-methods
# pylint: disable=invalid-name
import datetime
import time
from peewee import PrimaryKeyField, CharField, DateTimeField
from peewee import ForeignKeyField, TextField
from peewee import Model, OperationalError
from playhouse.db_url import connect
from pacifica.cart.config import get_config

DB = connect(get_config().get('database', 'peewee_url'))


def database_setup(attempts=0):
    """Setup and create the database from the db connection."""
    dbcon_attempts = get_config().getint('database', 'connect_attempts')
    dbcon_wait = get_config().getint('database', 'connect_wait')
    try:
        Cart.database_connect()
        for cls in [Cart, File]:
            cls.create_table(fail_silently=True)
        Cart.database_close()
    except OperationalError:
        # couldnt connect, potentially wait and try again
        if attempts < dbcon_attempts:
            # wait specified time to try reconnecting
            time.sleep(dbcon_wait)
            attempts += 1
            database_setup(attempts)
        raise OperationalError('Failed database connect retry.')


class CartBase(Model):
    """Base Cart Model class."""

    @classmethod
    def atomic(cls):
        """Do the DB atomic bits."""
        # pylint: disable=no-member
        return cls._meta.database.atomic()
        # pylint: enable=no-member

    @classmethod
    def database_connect(cls):
        """
        Make sure database is connected.

        Dont reopen connection.
        """
        # pylint: disable=no-member
        if not cls._meta.database.is_closed():
            cls._meta.database.close()
        cls._meta.database.connect()
        # pylint: enable=no-member

    @classmethod
    def database_close(cls):
        """Close the database connection."""
        # pylint: disable=no-member
        if not cls._meta.database.is_closed():
            cls._meta.database.close()
        # pylint: enable=no-member

    class Meta(object):
        """Meta object containing the database connection."""

        database = DB  # This model uses the pacifica_cart database.

    def reload(self):
        """Reload my current state from the DB."""
        newer_self = self.get(self._meta.primary_key == getattr(
            self, self._meta.primary_key.name))
        for field_name in self._meta.fields.keys():
            val = getattr(newer_self, field_name)
            setattr(self, field_name, val)
        self._dirty.clear()


class Cart(CartBase):
    """Cart object model."""

    id = PrimaryKeyField()
    cart_uid = CharField(default=1)
    bundle_path = CharField(default='')
    creation_date = DateTimeField(default=datetime.datetime.now)
    updated_date = DateTimeField(default=datetime.datetime.now)
    deleted_date = DateTimeField(null=True)
    status = TextField(default='waiting')
    error = TextField(default='')


class File(CartBase):
    """File object model to keep track of what's been downloaded for a cart."""

    id = PrimaryKeyField()
    cart = ForeignKeyField(Cart, to_field='id')
    file_name = CharField(default='')
    bundle_path = CharField(default='')
    hash_type = CharField(null=True)
    hash_value = CharField(null=True)
    status = TextField(default='waiting')
    error = TextField(default='')
