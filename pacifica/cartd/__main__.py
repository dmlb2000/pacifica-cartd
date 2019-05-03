#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Pacifica Cart Interface.

This is the main program that starts the WSGI server.
The core of the server code is in cart_interface.py.
"""
from time import sleep
from argparse import ArgumentParser, SUPPRESS
from threading import Thread
import cherrypy
from peewee import OperationalError, PeeweeException
from .orm import OrmSync, CartSystem, SCHEMA_MAJOR, SCHEMA_MINOR
from .rest import CartRoot, error_page_default
from .globals import CHERRYPY_CONFIG, CONFIG_FILE


def stop_later(doit=False):
    """Used for unit testing stop after 60 seconds."""
    if not doit:  # pragma: no cover
        return

    def sleep_then_exit():
        """
        Sleep for 60 seconds then call cherrypy exit.

        Hopefully this is long enough for the end-to-end tests to finish
        """
        sleep(60)
        cherrypy.engine.exit()
    sleep_thread = Thread(target=sleep_then_exit)
    sleep_thread.daemon = True
    sleep_thread.start()


def main():
    """Main method to start the httpd server."""
    parser = ArgumentParser(description='Run the cart server.')
    parser.add_argument('-c', '--config', metavar='CONFIG', type=str,
                        default=CONFIG_FILE, dest='config',
                        help='cart config file')
    parser.add_argument('--cpconfig', metavar='CONFIG', type=str,
                        default=CHERRYPY_CONFIG, dest='cpconfig',
                        help='cherrypy config file')
    parser.add_argument('-p', '--port', metavar='PORT', type=int,
                        default=8081, dest='port',
                        help='port to listen on')
    parser.add_argument('-a', '--address', metavar='ADDRESS',
                        default='127.0.0.1', dest='address',
                        help='address to listen on')
    parser.add_argument('--stop-after-a-moment', help=SUPPRESS,
                        default=False, dest='stop_later',
                        action='store_true')
    args = parser.parse_args()
    OrmSync.dbconn_blocking()
    if not CartSystem.is_safe():
        raise OperationalError('Database version too old {} update to {}'.format(
            '{}.{}'.format(*(CartSystem.get_version())),
            '{}.{}'.format(SCHEMA_MAJOR, SCHEMA_MINOR)
        ))
    stop_later(args.stop_later)
    cherrypy.config.update({'error_page.default': error_page_default})
    cherrypy.config.update({
        'server.socket_host': args.address,
        'server.socket_port': args.port
    })
    cherrypy.quickstart(CartRoot(), '/', args.cpconfig)


def cmd():
    """Main admin command line tool."""
    parser = ArgumentParser(description='Cart admin tool.')
    parser.add_argument(
        '-c', '--config', metavar='CONFIG', type=str, default=CONFIG_FILE,
        dest='config', help='cart config file'
    )
    subparsers = parser.add_subparsers(help='sub-command help')
    db_parser = subparsers.add_parser(
        'dbsync',
        description='Update or Create the Database.'
    )
    db_parser.set_defaults(func=dbsync)
    dbchk_parser = subparsers.add_parser(
        'dbchk',
        description='Check database against current version.'
    )
    dbchk_parser.add_argument(
        '--equal', default=False,
        dest='check_equal', action='store_true'
    )
    dbchk_parser.set_defaults(func=dbchk)
    args = parser.parse_args()
    return args.func(args)


def bool2cmdint(command_bool):
    """Convert a boolean to either 0 for true  or -1 for false."""
    if command_bool:
        return 0
    return -1


def dbchk(args):
    """Check the database for the version running."""
    OrmSync.dbconn_blocking()
    if args.check_equal:
        return bool2cmdint(CartSystem.is_equal())
    return bool2cmdint(CartSystem.is_safe())


def dbsync(_args):
    """Create or update the database."""
    OrmSync.dbconn_blocking()
    try:
        CartSystem.get_version()
    except PeeweeException:
        OrmSync.dbconn_blocking()
        return OrmSync.create_tables()
    return OrmSync.update_tables()


if __name__ == '__main__':
    main()
