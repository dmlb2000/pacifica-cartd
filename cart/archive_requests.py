"""Module that is used by the cart to send requests to the
archive interface
"""
from __future__ import absolute_import
from StringIO import StringIO
import pycurl
from cart.cart_env_globals import  ARCHIVE_INTERFACE_URL


class ArchiveRequests(object):
    """class that supports all the requests to the archive
    interface
    """

    def __init__(self):
        self._url = ARCHIVE_INTERFACE_URL

    def pull_file(self, archive_filename, cart_filepath):
        """Performs a curl that will attempt to write
        the contents of a file from the archive interface
        to the specified cart filepath
        """
        mycurl = pycurl.Curl()
        mycurl.setopt(mycurl.URL, str(self._url + archive_filename))
        with open(cart_filepath, 'w+') as myfile:
            mycurl.setopt(mycurl.WRITEFUNCTION, myfile.write)
            mycurl.perform()
        mycurl.close()

    def stage_file(self, file_name):
        """Sends a post to the archive interface telling it to stage the file
        """

        mycurl = pycurl.Curl()
        mycurl.setopt(mycurl.URL, str(self._url + file_name))
        mycurl.setopt(mycurl.POST, True)
        mycurl.perform()
        mycurl.close()


    def status_file(self, file_name):
        """Gets a status from the  archive interface via Head and
        returns response """

        storage = StringIO()
        mycurl = pycurl.Curl()
        mycurl.setopt(mycurl.CUSTOMREQUEST, "HEAD")
        mycurl.setopt(mycurl.URL, str(self._url + file_name))
        mycurl.setopt(mycurl.NOBODY, False)
        mycurl.setopt(mycurl.WRITEFUNCTION, storage.write)
        mycurl.perform()
        mycurl.close()
        content = storage.getvalue()
        return content
