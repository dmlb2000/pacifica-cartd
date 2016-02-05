#!/usr/bin/python
"""
Primary celery process.
"""
from __future__ import absolute_import
import os

from celery import Celery
BROKER_URL = 'amqp://guest:guest@'\
             +os.environ['AMQP_PORT_5672_TCP_ADDR']\
             +':'+os.environ['AMQP_PORT_5672_TCP_PORT']+'//'
MYSQL_PASS = os.environ['MYSQL_ENV_MYSQL_PASSWORD']
MYSQL_USER = os.environ['MYSQL_ENV_MYSQL_USER']
MYSQL_PORT = os.environ['MYSQL_PORT_3306_TCP_PORT']
MYSQL_ADDR = os.environ['MYSQL_PORT_3306_TCP_ADDR']
MYSQL_DATABASE = os.environ['MYSQL_ENV_MYSQL_DATABASE']
VOLUME_PATH = os.environ['VOLUME_PATH']
ARCHIVE_INTERFACE_URL = os.environ['ARCHIVE_INTERFACE_URL']
CART_APP = Celery('cart',
                  broker=BROKER_URL,
                  backend="amqp",
                  include=['cart.tasks'])

# Optional configuration, see the application user guide.
CART_APP.conf.update(
    CELERY_TASK_RESULT_EXPIRES=3600,
)

if __name__ == '__main__':
    CART_APP.start()
