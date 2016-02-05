from peewee import *
from playhouse.db_url import connect
import os
import datetime
from cart.celery import cart_app, MYSQL_USER, MYSQL_PASS, MYSQL_ADDR, MYSQL_DATABASE, MYSQL_PORT

db = MySQLDatabase(MYSQL_DATABASE, host=MYSQL_ADDR, port=int(MYSQL_PORT), user=MYSQL_USER, passwd=MYSQL_PASS)

def database_setup():
    db.connect()
    db.create_tables([Cart, File], safe=True)
    db.close()

class Cart(Model):
    id = PrimaryKeyField()
    cart_uid = CharField(default=1)
    bundle_path = CharField(default="")
    creation_date = DateTimeField(default=datetime.datetime.now())
    updated_date = DateTimeField(default=datetime.datetime.now())
    deleted_date = DateTimeField(null=True)
    status = TextField(default="waiting")
    error = TextField(default="")

    class Meta:
        database = db # This model uses the pacifica_cart database.

class File(Model):
    id = PrimaryKeyField()
    cart = ForeignKeyField(Cart, to_field="id")
    file_name = CharField(default="")
    bundle_path = CharField(default="")
    status = TextField(default="waiting")
    error = TextField(default="")

    class Meta:
        database = db # This model uses the pacifica_cart database.
