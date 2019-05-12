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
from json import dumps
from jsonschema import validate
from six import PY2
import cherrypy
from cherrypy.lib import static
from .tasks import stage_files, CART_APP
from .utils import Cartutils, parse_size
from .orm import Cart, CartTasks
from .config import get_config

if PY2:  # pragma: no cover only works with one version of python
    # pylint: disable=invalid-name
    bytes_type = str
    # pylint: enable=invalid-name
else:  # pragma: no cover only will work on one version of python
    # pylint: disable=invalid-name
    def bytes_type(unicode_obj):
        """Convert the unicode object into bytes."""
        return bytes(unicode_obj, 'UTF-8')
    # pylint: enable=invalid-name


def error_page_default(**kwargs):
    """The default error page should always enforce json."""
    cherrypy.response.headers['Content-Type'] = 'application/json'
    return dumps({
        'status': kwargs['status'],
        'message': kwargs['message'],
        'traceback': kwargs['traceback'],
        'version': kwargs['version']
    })


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

    json_schema = {
        'type': 'object',
        'properties': {
            'fileids': {
                'type': 'array',
                'items': {
                    'type': 'object',
                    'properties': {
                        'id': {'type': ['integer', 'string']},
                        'path': {'type': 'string'},
                        'hashtype': {'type': 'string'},
                        'hashsum': {'type': 'string'},
                    },
                    'required': ['id', 'path', 'hashtype', 'hashsum']
                }
            }
        },
        'required': [
            'fileids'
        ]
    }
    exposed = True

    # Cherrypy requires these named methods.
    # pylint: disable=invalid-name
    @staticmethod
    def GET(uid=None, **kwargs):
        """Download the tar file created by the cart."""
        if not uid:
            cherrypy.response.headers['Content-Type'] = 'application/json'
            return bytes_type(dumps({'message': 'Pacifica Cartd Interface Up and Running'}))
        rtn_name = kwargs.get(
            'filename', 'data_' + datetime.now().strftime('%Y_%m_%d_%H_%M_%S') + '.tar')
        # get the bundle path if available
        cart_utils = Cartutils()
        Cart.database_connect()
        cart_path = cart_utils.available_cart(uid)
        Cart.database_close()
        if cart_path is False:
            # cart not ready
            cherrypy.response.status = '202 Accepted'
            return bytes_type('The cart is not ready for download.')
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
            cherrypy.response.stream = True
            cherrypy.response.headers['Content-Type'] = 'application/octet-stream'
            cherrypy.response.headers['Content-Disposition'] = 'attachment; filename={}'.format(
                rtn_name)

            xfer_size = parse_size(get_config().get('cartd', 'transfer_size'))

            def read():
                """read some size from rfd."""
                buf = rfd.read(xfer_size)
                while buf:
                    yield buf
                    buf = rfd.read(xfer_size)
                wthread.join()
            return read()
        elif os.path.isfile(cart_path):
            return static.serve_file(
                cart_path,
                'application/octet-stream',
                'attachment',
                rtn_name
            )
        raise cherrypy.HTTPError(404, 'Not Found')

    # Cherrypy requires these named methods.
    # pylint: disable=invalid-name
    @staticmethod
    @cherrypy.tools.json_out()
    def HEAD(uid):
        """Get the status of a carts tar file."""
        cart_utils = Cartutils()
        Cart.database_connect()
        status, message = cart_utils.cart_status(uid)
        Cart.database_close()
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
    @classmethod
    @cherrypy.tools.json_out()
    @cherrypy.tools.json_in()
    def POST(cls, uid):
        """Get all the files locally and bundled."""
        data = cherrypy.request.json
        validate(data, cls.json_schema)
        bundle = data.get(
            'bundle',
            get_config().getboolean(
                'cartd',
                'bundle_task'
            )
        )
        Cart.database_connect()
        mycart = Cart(cart_uid=uid, status='staging', bundle=bundle)
        mycart.save()
        files_task = CartTasks(
            celery_task_id=str(stage_files.delay(data['fileids'], mycart.id)),
            cart_id=mycart.id
        )
        files_task.save()
        Cart.database_close()
        cherrypy.response.status = '201 Created'
        return {'message': 'Cart Processing has begun'}

    # Cherrypy requires these named methods.
    # pylint: disable=invalid-name
    @staticmethod
    @cherrypy.tools.json_out()
    def DELETE(uid):
        """Delete a cart that has been created."""
        cart_utils = Cartutils()
        Cart.database_connect()
        message = cart_utils.remove_cart(uid, CART_APP.control.revoke)
        Cart.database_close()
        if message is False:
            raise cherrypy.HTTPError(404, 'Not Found')
        return {'message': str(message)}
