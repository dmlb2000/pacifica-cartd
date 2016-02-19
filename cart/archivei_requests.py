from __future__ import absolute_import
from cart.cart_orm import Cart, File, DB, database_connect, database_close
from os import path
from cart.cart_env_globals import VOLUME_PATH, ARCHIVE_INTERFACE_URL, LRU_BUFFER_TIME
import os
import time
import json
import datetime
import errno
import psutil
import pycurl
from StringIO import StringIO


class archivei_requests:

    @staticmethod
    def pull_file(archive_filename, cart_filepath):
        """Performs a curl that will attempt to write
        the contents of a file from the archive interface
        to the specified cart filepath
        """
        c = pycurl.Curl()
        c.setopt(c.URL, str(ARCHIVE_INTERFACE_URL + archive_filename))
        with open(cart_filepath, 'w+') as f:
            c.setopt(c.WRITEFUNCTION, f.write)
            c.perform()
        c.close()

    @staticmethod
    def stage_file(file_name):
        """Sends a post to the archive interface telling it to stage the file """
        
        c = pycurl.Curl() 
        c.setopt(c.URL, str(ARCHIVE_INTERFACE_URL + file_name))
        c.setopt(c.POST, True)
        c.perform()
        c.close()
        


    @staticmethod        
    def status_file(file_name):
        """Gets a status from the  archive interface via Head and returns response """
        
        storage = StringIO()
        c = pycurl.Curl() 
        c.setopt(c.CUSTOMREQUEST, "HEAD")
        c.setopt(c.URL, str(ARCHIVE_INTERFACE_URL + file_name))
        c.setopt(c.NOBODY, False)
        c.setopt(c.WRITEFUNCTION, storage.write)
        c.perform()
        c.close()
        content = storage.getvalue()
        return content 