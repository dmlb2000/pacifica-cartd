#!/usr/bin/python
"""
Pacifica Cart Interface.

This is the main program that starts the WSGI server.
The core of the server code is in cart_interface.py.
"""
from json import dumps
import cherrypy
from cart.cart_orm import database_setup
from cart.cart_interface import CartRoot


def error_page_default(**kwargs):
    """The default error page should always enforce json."""
    cherrypy.response.headers['Content-Type'] = 'application/json'
    return dumps({
        'status': kwargs['status'],
        'message': kwargs['message'],
        'traceback': kwargs['traceback'],
        'version': kwargs['version']
    })


def main():
    """Main method to start the httpd server."""
    database_setup()
    cherrypy.quickstart(CartRoot(), '/', 'server.conf')


cherrypy.config.update({'error_page.default': error_page_default})
# pylint doesn't realize that application is actually a callable
# pylint: disable=invalid-name
application = cherrypy.Application(CartRoot(), '/', 'server.conf')
# pylint: enable=invalid-name
