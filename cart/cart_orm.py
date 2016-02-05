#!/usr/bin/python
"""
Cart Object Relational Model

Using PeeWee to implement the ORM.
"""
# disable this for classes Cart, File and Meta (within Cart and File)
# pylint: disable=too-few-public-methods
# pylint: disable=invalid-name
from peewee import MySQLDatabase, Model, PrimaryKeyField, CharField, DateTimeField
from peewee import ForeignKeyField, TextField
import datetime
from cart.celery import MYSQL_USER, MYSQL_PASS, MYSQL_ADDR, MYSQL_DATABASE, MYSQL_PORT

DB = MySQLDatabase(MYSQL_DATABASE,
                   host=MYSQL_ADDR,
                   port=int(MYSQL_PORT),
                   user=MYSQL_USER,
                   passwd=MYSQL_PASS)

def database_setup():
    """
    Setup and create the database from the db connection.
    """
    DB.connect()
    DB.create_tables([Cart, File], safe=True)
    DB.close()

class Cart(Model):
    """
    Cart object model
    """
    id = PrimaryKeyField()
    cart_uid = CharField(default=1)
    bundle_path = CharField(default="")
    creation_date = DateTimeField(default=datetime.datetime.now())
    updated_date = DateTimeField(default=datetime.datetime.now())
    deleted_date = DateTimeField(null=True)
    status = TextField(default="waiting")
    error = TextField(default="")

    class Meta(object):
        """
        Meta object containing the database connection
        """
        database = DB # This model uses the pacifica_cart database.

class File(Model):
    """
    File object model to keep track of what's been downloaded for a cart
    """
    id = PrimaryKeyField()
    cart = ForeignKeyField(Cart, to_field="id")
    file_name = CharField(default="")
    bundle_path = CharField(default="")
    status = TextField(default="waiting")
    error = TextField(default="")

    class Meta(object):
        """
        Meta object containing the database connection
        """
        database = DB # This model uses the pacifica_cart database.

