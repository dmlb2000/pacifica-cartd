import os

try:
    VOLUME_PATH = os.environ['VOLUME_PATH']
    #archive_int = os.getenv("ARCHIVE_INTERFACE_URL")
    if "ARCHIVE_INTERFACE_URL" in os.environ:
        ARCHIVE_INTERFACE_URL = os.getenv("ARCHIVE_INTERFACE_URL")
    else:
        ARCHIVE_INTERFACE_ADDR = os.environ['ARCHIVEI_PORT_8080_TCP_ADDR']
        ARCHIVE_INTERFACE_PORT = os.environ['ARCHIVEI_PORT_8080_TCP_PORT']
        # check if it already exists first, if not do this, else take the part that is filled out
        ARCHIVE_INTERFACE_URL = ('http://' + ARCHIVE_INTERFACE_ADDR + ':' + ARCHIVE_INTERFACE_PORT + '/')
    #buffer used for least recently used delete
    if "LRU_BUFFER_TIME" in os.environ:
        LRU_BUFFER_TIME = os.getenv("LRU_BUFFER_TIME")
    else:
        LRU_BUFFER_TIME = 0
except Exception as ex:
    print "Error with environment variable: " + str(ex)