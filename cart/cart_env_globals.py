"""
Used to load in all the carts environment variables
"""
import os
import logging


VOLUME_PATH = os.environ['VOLUME_PATH']
# see if archive interface is specified.  If not build it from
#container environment variables.
if "ARCHIVE_INTERFACE_URL" in os.environ:
    ARCHIVE_INTERFACE_URL = os.getenv("ARCHIVE_INTERFACE_URL")
else:
    ARCHIVE_INTERFACE_ADDR = os.environ['ARCHIVEI_PORT_8080_TCP_ADDR']
    ARCHIVE_INTERFACE_PORT = os.environ['ARCHIVEI_PORT_8080_TCP_PORT']
    ARCHIVE_INTERFACE_URL = ('http://' + ARCHIVE_INTERFACE_ADDR +
                             ':' + ARCHIVE_INTERFACE_PORT + '/')

#buffer used for least recently used delete
if "LRU_BUFFER_TIME" in os.environ:
    LRU_BUFFER_TIME = os.getenv("LRU_BUFFER_TIME")
else:
    LRU_BUFFER_TIME = 0

#database logging for query tracking
if "DATABASE_LOGGING" in os.environ:
    if os.getenv("DATABASE_LOGGING"):
        LOGGER = logging.getLogger('peewee')
        LOGGER.setLevel(logging.DEBUG)
        LOGGER.addHandler(logging.StreamHandler())

#Number of attempts to connect to database.  Default 3
if "DATABASE_CONNECT_ATTEMPTS" in os.environ:
    DATABASE_CONNECT_ATTEMPTS = os.getenv("DATABASE_CONNECT_ATTEMPTS")
else:
    DATABASE_CONNECT_ATTEMPTS = 3

#time between trying to reconnect to database.  Default 10 seconds
if "DATABASE_WAIT" in os.environ:
    DATABASE_WAIT = os.getenv("DATABASE_WAIT")
else:
    DATABASE_WAIT = 10

BROKER_URL = 'amqp://guest:guest@'\
             +os.environ['AMQP_PORT_5672_TCP_ADDR']\
             +':'+os.environ['AMQP_PORT_5672_TCP_PORT']+'//'
MYSQL_PASS = os.environ['MYSQL_ENV_MYSQL_PASSWORD']
MYSQL_USER = os.environ['MYSQL_ENV_MYSQL_USER']
MYSQL_PORT = os.environ['MYSQL_PORT_3306_TCP_PORT']
MYSQL_ADDR = os.environ['MYSQL_PORT_3306_TCP_ADDR']
MYSQL_DATABASE = os.environ['MYSQL_ENV_MYSQL_DATABASE']
