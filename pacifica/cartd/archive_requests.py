#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Module that is used by the cart to send requests to the archive interface."""
from __future__ import absolute_import
from time import sleep
from json import dumps
import hashlib
import requests
from .utils import parse_size
from .config import get_config


class ArchiveRequests:
    """Class that supports all the requests to the archive interface."""

    default_retry_count = 5
    default_retry_sleep = 1

    def __init__(self):
        """Constructor for setting the AI URL."""
        self._url = get_config().get('archiveinterface', 'url')

    # pylint: disable=too-many-arguments
    def pull_file(self, archive_filename, cart_filepath, hashval, hashtype, retry=None):
        """
        Pull file from AI.

        Performs a request that will attempt to write
        the contents of a file from the archive interface
        to the specified cart filepath
        """
        if retry is None:
            retry = self.default_retry_count
        while retry:
            try:
                self._pull_file(archive_filename, cart_filepath, hashval, hashtype)
                retry = 0
            except (requests.exceptions.RequestException, ValueError) as ex:
                if retry == 1:
                    raise ex
                sleep(self.default_retry_sleep)
                retry -= 1
    # pylint: enable=too-many-arguments

    def _pull_file(self, archive_filename, cart_filepath, hashval, hashtype):
        xfer_size = parse_size(get_config().get('cartd', 'transfer_size'))
        resp = requests.get(str(self._url + archive_filename), stream=True)
        if int(resp.status_code/100) == 5:
            raise requests.exceptions.RequestException('Status code is 500')
        myfile = open(cart_filepath, 'wb+')
        buf = resp.raw.read(xfer_size)
        myhash = hashlib.new(hashtype)
        while buf:
            myfile.write(buf)
            myhash.update(buf)
            buf = resp.raw.read(xfer_size)
        myfile.close()
        myhashval = myhash.hexdigest()
        if myhashval != hashval:
            raise ValueError('File hash does not match provided hash')

    def stage_file(self, file_name):
        """Send a post to the archive interface telling it to stage the file."""
        resp = requests.post(str(self._url + file_name))
        if str(resp.status_code) == '500':
            raise requests.exceptions.RequestException(str(dumps(resp.text)))

    @staticmethod
    def _status_dict(headers, file_name):
        """Return status dictionary from http response headers."""
        return {
            'message': headers['x-pacifica-messsage'],
            'file': file_name,
            'filesize': headers['x-content-length'],
            'ctime': headers['x-pacifica-ctime'],
            'mtime': headers['last-modified'],
            'bytes_per_level': headers['x-pacifica-bytes-per-level'],
            'file_storage_media': headers['x-pacifica-file-storage-media']
        }

    def status_file(self, file_name):
        """Get a status from the  archive interface via Head and returns response."""
        resp = requests.head(str(self._url + file_name))
        return dumps(self._status_dict(resp.headers, file_name))
