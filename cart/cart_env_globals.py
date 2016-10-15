"""
Used to load in all the carts environment variables

Wrapped all in if statements so that they can be used in
unit test environment
"""
import os
import logging


VOLUME_PATH = os.getenv("VOLUME_PATH", '/tmp/')

# see if archive interface is specified.  If not build it from
#container environment variables.
ARCHIVE_INTERFACE_ADDR = os.getenv('ARCHIVEI_PORT_8080_TCP_ADDR', 'localhost')
ARCHIVE_INTERFACE_PORT = os.getenv('ARCHIVEI_PORT_8080_TCP_PORT', '8080')
ARCHIVE_INTERFACE_URL = ('http://' + ARCHIVE_INTERFACE_ADDR +
                         ':' + ARCHIVE_INTERFACE_PORT + '/')
ARCHIVE_INTERFACE_URL = os.getenv("ARCHIVE_INTERFACE_URL", ARCHIVE_INTERFACE_URL)

#buffer used for least recently used delete
LRU_BUFFER_TIME = os.getenv("LRU_BUFFER_TIME", 0)

#database logging for query tracking
DATABASE_LOGGING = os.getenv('DATABASE_LOGGING', False)
if DATABASE_LOGGING:
    LOGGER = logging.getLogger('peewee')
    LOGGER.setLevel(logging.DEBUG)
    LOGGER.addHandler(logging.StreamHandler())

#Number of attempts to connect to database.  Default 3
DATABASE_CONNECT_ATTEMPTS = os.getenv("DATABASE_CONNECT_ATTEMPTS", 3)

#time between trying to reconnect to database.  Default 10 seconds
DATABASE_WAIT = os.getenv("DATABASE_WAIT", 10)

#amqp addr and port variables
AMQP_ADDR = os.getenv("AMQP_PORT_5672_TCP_ADDR", 'localhost')
AMQP_PORT = os.getenv("AMQP_PORT_5672_TCP_PORT", '5672')

BROKER_URL = 'amqp://guest:guest@'\
             +AMQP_ADDR\
             +':'+AMQP_PORT+'//'

BROKER_URL = os.getenv('BROKER_URL', BROKER_URL)

#mysql variables
MYSQL_PASS = os.getenv("MYSQL_ENV_MYSQL_PASSWORD", 'root')
MYSQL_USER = os.getenv("MYSQL_ENV_MYSQL_USER", 'root')
MYSQL_PORT = os.getenv("MYSQL_PORT_3306_TCP_PORT", '3306')
MYSQL_ADDR = os.getenv("MYSQL_PORT_3306_TCP_ADDR", 'localhost')
MYSQL_DATABASE = os.getenv("MYSQL_ENV_MYSQL_DATABASE", 'cartd')
