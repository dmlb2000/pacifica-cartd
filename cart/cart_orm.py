#!/usr/bin/python
"""
Cart Object Relational Model

Using PeeWee to implement the ORM.
"""
# disable this for classes Cart, File and Meta (within Cart and File)
# pylint: disable=too-few-public-methods
# pylint: disable=invalid-name
import datetime
import time
from peewee import MySQLDatabase, PrimaryKeyField, CharField, DateTimeField
from peewee import ForeignKeyField, TextField
from peewee import Model, ProgrammingError, OperationalError
from cart.cart_env_globals import MYSQL_USER, MYSQL_PASS, MYSQL_ADDR
from cart.cart_env_globals import MYSQL_PORT, MYSQL_DATABASE
from cart.cart_env_globals import DATABASE_CONNECT_ATTEMPTS, DATABASE_WAIT


DB = MySQLDatabase(MYSQL_DATABASE,
                   host=MYSQL_ADDR,
                   port=int(MYSQL_PORT),
                   user=MYSQL_USER,
                   passwd=MYSQL_PASS)

def database_setup(attempts=0):
    """
    Setup and create the database from the db connection.
    """
    try:
        database_connect()
        DB.create_tables([Cart, File], safe=True)
        database_close()
    except OperationalError:
        #couldnt connect, potentially wait and try again
        if attempts < DATABASE_CONNECT_ATTEMPTS:
            #wait specified time to try reconnecting
            time.sleep(DATABASE_WAIT)
            attempts += 1
            database_setup(attempts)


def database_connect():
    """Makes sure database is connected.  Trying to connect a second
    time doesnt cause any problems"""
    DB.connect()

def database_close():
    """Closes the database connection. Closing already closed database
    throws an error so catch it and continue on"""
    try:
        DB.close()
    except ProgrammingError:
        #error for closing an already closed database so continue on
        return

class Cart(Model):
    """
    Cart object model
    """
    id = PrimaryKeyField()
    cart_uid = CharField(default=1)
    bundle_path = CharField(default="")
    creation_date = DateTimeField(default=datetime.datetime.now)
    updated_date = DateTimeField(default=datetime.datetime.now)
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

