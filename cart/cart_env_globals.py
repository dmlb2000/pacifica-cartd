"""
Used to load in all the carts environment variables

Wrapped all in if statements so that they can be used in
unit test environment
"""
import os
import logging


if 'VOLUME_PATH' in os.environ:
    VOLUME_PATH = os.getenv("VOLUME_PATH")
else:
    VOLUME_PATH = '/tmp/'
# see if archive interface is specified.  If not build it from
#container environment variables.
if "ARCHIVE_INTERFACE_URL" in os.environ:
    ARCHIVE_INTERFACE_URL = os.getenv("ARCHIVE_INTERFACE_URL")
elif 'ARCHIVEI_PORT_8080_TCP_ADDR' in os.environ:
    ARCHIVE_INTERFACE_ADDR = os.environ['ARCHIVEI_PORT_8080_TCP_ADDR']
    ARCHIVE_INTERFACE_PORT = os.environ['ARCHIVEI_PORT_8080_TCP_PORT']
    ARCHIVE_INTERFACE_URL = ('http://' + ARCHIVE_INTERFACE_ADDR +
                             ':' + ARCHIVE_INTERFACE_PORT + '/')
else:
    ARCHIVE_INTERFACE_URL = ('http://localhost:8080/')

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


#amqp addr and port variables
if "AMQP_PORT_5672_TCP_ADDR" in os.environ:
    AMQP_ADDR = os.getenv("AMQP_PORT_5672_TCP_ADDR")
else:
    AMQP_ADDR = "localhost"

if "AMQP_PORT_5672_TCP_PORT" in os.environ:
    AMQP_PORT = os.getenv("AMQP_PORT_5672_TCP_PORT")
else:
    AMQP_PORT = "localhost"

BROKER_URL = 'amqp://guest:guest@'\
             +AMQP_ADDR\
             +':'+AMQP_PORT+'//'

#mysql variables
if "MYSQL_ENV_MYSQL_PASSWORD" in os.environ:
    MYSQL_PASS = os.getenv("MYSQL_ENV_MYSQL_PASSWORD")
else:
    MYSQL_PASS = "root"

if "MYSQL_ENV_MYSQL_USER" in os.environ:
    MYSQL_USER = os.getenv("MYSQL_ENV_MYSQL_USER")
else:
    MYSQL_USER = "root"

if "MYSQL_PORT_3306_TCP_PORT" in os.environ:
    MYSQL_PORT = os.getenv("MYSQL_PORT_3306_TCP_PORT")
else:
    MYSQL_PORT = "3306"

if "MYSQL_PORT_3306_TCP_ADDR" in os.environ:
    MYSQL_ADDR = os.getenv("MYSQL_PORT_3306_TCP_ADDR")
else:
    MYSQL_ADDR = "localhost"

if "MYSQL_ENV_MYSQL_DATABASE" in os.environ:
    MYSQL_DATABASE = os.getenv("MYSQL_ENV_MYSQL_DATABASE")
else:
    MYSQL_DATABASE = "test"
