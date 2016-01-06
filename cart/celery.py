from __future__ import absolute_import
import os

from celery import Celery
BROKER_URL = 'amqp://guest:guest@'+os.environ['AMQP_PORT_5672_TCP_ADDR']+':'+os.environ['AMQP_PORT_5672_TCP_PORT']+'//'
MYSQL_PASS = os.environ['MYSQL_ENV_MYSQL_ROOT_PASSWORD']
MYSQL_PORT = os.environ['MYSQL_PORT_3306_TCP_PORT']
MYSQL_ADDR = os.environ['MYSQL_PORT_3306_TCP_ADDR']
MYSQL_DATABASE = os.environ['MYSQL_ENV_MYSQL_DATABASE']
cart_app = Celery('cart',
             broker=BROKER_URL,
             backend="amqp",
             include=['cart.tasks'])

# Optional configuration, see the application user guide.
cart_app.conf.update(
    CELERY_TASK_RESULT_EXPIRES=3600,
)

if __name__ == '__main__':
    cart_app.start()
