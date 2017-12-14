#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Pacifica Cart Interface.

This is the main program that starts the WSGI server.
The core of the server code is in cart_interface.py.
"""
from argparse import ArgumentParser
from json import dumps
import cherrypy
from cart.cart_orm import database_setup
from cart.cart_interface import CartRoot
from cart.cart_env_globals import CHERRYPY_CONFIG


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
    parser = ArgumentParser(description='Run the cart server.')
    parser.add_argument('-c', '--config', metavar='CONFIG', type=str,
                        default=CHERRYPY_CONFIG, dest='config',
                        help='cherrypy config file')
    parser.add_argument('-p', '--port', metavar='PORT', type=int,
                        default=8081, dest='port',
                        help='port to listen on')
    parser.add_argument('-a', '--address', metavar='ADDRESS',
                        default='localhost', dest='address',
                        help='address to listen on')
    args = parser.parse_args()
    database_setup()
    cherrypy.config.update({
        'server.socket_host': args.address,
        'server.socket_port': args.port
    })
    cherrypy.quickstart(CartRoot(), '/', args.config)


if __name__ == '__main__':
    main()
