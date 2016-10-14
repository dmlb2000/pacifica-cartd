"""Module that is used by the cart to send requests to the
archive interface
"""

from __future__ import absolute_import
from json import dumps
import requests
from cart.cart_env_globals import  ARCHIVE_INTERFACE_URL


class ArchiveRequests(object):
    """class that supports all the requests to the archive
    interface
    """

    def __init__(self):
        self._url = ARCHIVE_INTERFACE_URL

    def pull_file(self, archive_filename, cart_filepath):
        """Performs a request that will attempt to write
        the contents of a file from the archive interface
        to the specified cart filepath
        """
        resp = requests.get(str(self._url + archive_filename), stream=True)
        myfile = open(cart_filepath, 'wb+')
        buf = resp.raw.read(1024)
        while len(buf):
            myfile.write(buf)
            buf = resp.raw.read(1024)
        myfile.close()

    def stage_file(self, file_name):
        """Sends a post to the archive interface telling it to stage the file
        """
        requests.post(str(self._url + file_name))

    @staticmethod
    def _status_dict(headers, file_name):
        """Return status dictionary from http response headers"""
        return {
            'message': headers['x-pacifica-messsage'],
            'file': file_name,
            'filesize': headers['content-length'],
            'ctime': headers['x-pacifica-ctime'],
            'mtime': headers['last-modified'],
            'bytes_per_level': headers['x-pacifica-bytes-per-level'],
            'file_storage_media': headers['x-pacifica-file-storage-media']
        }

    def status_file(self, file_name):
        """Gets a status from the  archive interface via Head and
        returns response """

        resp = requests.head(str(self._url + file_name))
        return dumps(self._status_dict(resp.headers, file_name))
