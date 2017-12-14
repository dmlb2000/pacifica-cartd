#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Class for the cart interface.

Allows API to file interactions.
"""
import os
from threading import Thread
from datetime import datetime
from sys import stderr
from tarfile import TarFile
import cherrypy
from cart.tasks import create_cart
from cart.cart_utils import Cartutils


BLOCK_SIZE = 1 << 20


class CartInterfaceError(Exception):
    """
    CartInterfaceError.

    Basic exception class for this module.
    Will be used to throw exceptions up to the top level of the application.
    """

    pass


class CartRoot(object):
    """
    Define the methods that can be used for cart request types.

    Doctest for the cart generator class
    HPSS Doc Tests
    """

    exposed = True

    # Cherrypy requires these named methods.
    # pylint: disable=invalid-name
    @staticmethod
    @cherrypy.config(**{'response.stream': True})
    def GET(uid, **kwargs):
        """Download the tar file created by the cart."""
        rtn_name = kwargs.get(
            'filename', 'data_' + datetime.now().strftime('%Y_%m_%d_%H_%M_%S') + '.tar')
        # get the bundle path if available
        cart_utils = Cartutils()
        cart_path = cart_utils.available_cart(uid)
        if cart_path is False:
            # cart not ready
            cherrypy.response.status = 202
            return 'The cart is not ready for download.'
        elif cart_path is None:
            # cart not found
            raise cherrypy.HTTPError(
                404, 'The cart does not exist or has already been deleted')
        if os.path.isdir(cart_path):
            # give back bundle here
            stderr.flush()
            # want to stream the tar file out
            (rpipe, wpipe) = os.pipe()
            rfd = os.fdopen(rpipe, 'rb')
            wfd = os.fdopen(wpipe, 'wb')

            def do_work():
                """The child thread writes the data to the pipe."""
                mytar = TarFile.open(fileobj=wfd, mode='w|')
                mytar.add(cart_path, arcname=rtn_name.replace('.tar', ''))
                mytar.close()
                wfd.close()
            # open the pipe as a file
            wthread = Thread(target=do_work)
            wthread.daemon = True
            wthread.start()
            cherrypy.response.headers['Content-Type'] = 'application/octet-stream'
            cherrypy.response.headers['Content-Disposition'] = 'attachment; filename={}'.format(
                rtn_name)

            def read():
                """read some size from rfd."""
                buf = rfd.read(BLOCK_SIZE)
                while buf:
                    yield buf
                    buf = rfd.read(BLOCK_SIZE)
                wthread.join()
            return read()
        raise cherrypy.HTTPError(404, 'Not Found')

    # Cherrypy requires these named methods.
    # pylint: disable=invalid-name
    @staticmethod
    @cherrypy.tools.json_out()
    def HEAD(uid):
        """Get the status of a carts tar file."""
        cart_utils = Cartutils()
        status, message = cart_utils.cart_status(uid)
        cherrypy.response.headers['X-Pacifica-Status'] = status
        cherrypy.response.headers['X-Pacifica-Message'] = message
        if status == 'error':
            if 'No cart with uid' in message:
                raise cherrypy.HTTPError(404, 'Not Found')
            else:
                raise cherrypy.HTTPError(500, 'Internal Server Error')
        cherrypy.response.status = 204
        return 'No Content'

    # Cherrypy requires these named methods.
    # pylint: disable=invalid-name
    @staticmethod
    @cherrypy.tools.json_out()
    @cherrypy.tools.json_in()
    def POST(uid):
        """Get all the files locally and bundled."""
        data = cherrypy.request.json
        file_ids = data['fileids']
        create_cart(file_ids, uid)
        cherrypy.response.status = '201 Created'
        return {'message': 'Cart Processing has begun'}

    # Cherrypy requires these named methods.
    # pylint: disable=invalid-name
    @staticmethod
    @cherrypy.tools.json_out()
    def DELETE(uid):
        """Delete a cart that has been created."""
        cart_utils = Cartutils()
        message = cart_utils.remove_cart(uid)
        if message is False:
            raise cherrypy.HTTPError(404, 'Not Found')
        return {'message': str(message)}
