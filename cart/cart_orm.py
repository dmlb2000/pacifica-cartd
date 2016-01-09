from peewee import *
from playhouse.db_url import connect
import os
import datetime
from cart.celery import cart_app, MYSQL_USER, MYSQL_PASS, MYSQL_ADDR, MYSQL_DATABASE, MYSQL_PORT

db = MySQLDatabase(MYSQL_DATABASE, host=MYSQL_ADDR, port=int(MYSQL_PORT), user=MYSQL_USER, passwd=MYSQL_PASS)

def database_setup():
    db.connect()
    db.create_tables([Cart], safe=True)

class Cart(Model):
    id = PrimaryKeyField()
    cart_uuid = CharField(default=1)
    creation_date = DateTimeField(default=datetime.datetime.now())
    updated_date = DateTimeField(default=datetime.datetime.now())
    deleted_date = DateTimeField(default=datetime.datetime.now())
    status = TextField(default="")

    class Meta:
        database = db # This model uses the pacifica_cart database.
