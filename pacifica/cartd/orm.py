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
from peewee import PrimaryKeyField, IntegerField, CharField, DateTimeField
from peewee import ForeignKeyField, TextField, BooleanField
from peewee import Model, OperationalError
from playhouse.migrate import SchemaMigrator, migrate
from playhouse.db_url import connect
from .config import get_config

SCHEMA_MAJOR = 2
SCHEMA_MINOR = 0
DB = connect(get_config().get('database', 'peewee_url'))


class OrmSync(object):
    """
    Special module for syncing the orm.

    This module should incorporate a schema migration strategy.

    The supported versions migrating forward must be in a versions array
    containing tuples for major and minor versions.

    The version tuples are directly translated to method names in the
    orm_update class for the update between those versions.

    Example Version Control::

      class orm_update:
        versions = [
          (0, 1),
          (0, 2),
          (1, 0),
          (1, 1)
        ]

        def update_0_1_to_0_2():
            pass
        def update_0_2_to_1_0():
            pass

    The body of the update should follow peewee migration practices.
    http://docs.peewee-orm.com/en/latest/peewee/playhouse.html#migrate
    """

    versions = [
        (0, 1),
        (1, 0),
        (2, 0)
    ]

    @staticmethod
    def dbconn_blocking():
        """Wait for the db connection."""
        dbcon_attempts = get_config().getint('database', 'connect_attempts')
        dbcon_wait = get_config().getint('database', 'connect_wait')
        while dbcon_attempts:
            try:
                Cart.database_connect()
                return
            except OperationalError:
                # couldnt connect, potentially wait and try again
                time.sleep(dbcon_wait)
                dbcon_attempts -= 1
        raise OperationalError('Failed database connect retry.')

    @staticmethod
    def create_tables():
        """Create the tables if they don't exist."""
        for cls in [CartSystem, Cart, File, CartTasks]:
            if not cls.table_exists():
                cls.create_table()
        CartSystem.get_or_create_version()

    @classmethod
    def update_0_1_to_1_0(cls):
        """Update by adding the boolean column."""
        migrator = SchemaMigrator(DB)
        migrate(
            migrator.add_column(
                'cart',
                'bundle',
                BooleanField(default=False, null=True)
            )
        )

    @classmethod
    def update_1_0_to_2_0(cls):
        """Update by adding the boolean column."""
        CartTasks.create_table()

    @classmethod
    def update_tables(cls):
        """Update the database to the current version."""
        verlist = cls.versions
        db_ver = CartSystem.get_version()
        if verlist.index(verlist[-1]) == verlist.index(db_ver):
            # we have the current version don't update
            return
        with Cart.atomic():
            for db_ver in verlist[verlist.index(db_ver):-1]:
                next_db_ver = verlist[verlist.index(db_ver)+1]
                method_name = 'update_{}_to_{}'.format(
                    '{}_{}'.format(*db_ver),
                    '{}_{}'.format(*next_db_ver)
                )
                getattr(cls, method_name)()
            CartSystem.drop_table()
            CartSystem.create_table()
            CartSystem.get_or_create_version()


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


class CartSystem(CartBase):
    """Cart Schema Version Model."""

    part = CharField(primary_key=True)
    value = IntegerField(default=-1)

    @classmethod
    def get_or_create_version(cls):
        """Set or create the current version of the schema."""
        major = cls.get_or_create(part='major', value=SCHEMA_MAJOR)
        minor = cls.get_or_create(part='minor', value=SCHEMA_MINOR)
        return (major, minor)

    @classmethod
    def get_version(cls):
        """Get the current version as a tuple."""
        return (cls.get(part='major').value, cls.get(part='minor').value)

    @classmethod
    def is_equal(cls):
        """Check to see if schema version matches code version."""
        major, minor = cls.get_version()
        return major == SCHEMA_MAJOR and minor == SCHEMA_MINOR

    @classmethod
    def is_safe(cls):
        """Check to see if the schema version is safe for the code."""
        major, _minor = cls.get_version()
        return major == SCHEMA_MAJOR


class Cart(CartBase):
    """Cart object model."""

    id = PrimaryKeyField()
    cart_uid = CharField(default=1)
    bundle_path = CharField(default='')
    bundle = BooleanField(default=False, null=True)
    creation_date = DateTimeField(default=datetime.datetime.now)
    updated_date = DateTimeField(default=datetime.datetime.now)
    deleted_date = DateTimeField(null=True)
    status = TextField(default='waiting')
    error = TextField(default='')


class CartTasks(CartBase):
    """List of tasks based on a cart ID."""

    cart_id = ForeignKeyField(Cart, index=True)
    celery_task_id = CharField(default='')


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
