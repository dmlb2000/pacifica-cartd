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
