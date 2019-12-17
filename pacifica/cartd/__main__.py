#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Pacifica Cart Interface.

This is the main program that starts the WSGI server.
The core of the server code is in cart_interface.py.
"""
from __future__ import print_function
from sys import argv as sys_argv
from time import sleep
from argparse import ArgumentParser, SUPPRESS
from threading import Thread
from datetime import timedelta, datetime
import json
import yaml
import cherrypy
from peewee import OperationalError, PeeweeException
from .orm import File, OrmSync, CartSystem, SCHEMA_MAJOR, SCHEMA_MINOR
from .rest import CartRoot, error_page_default
from .globals import CHERRYPY_CONFIG, CONFIG_FILE
from .fixit import fixit
from .utils import Cartutils
from .tasks import CART_APP


def objstr_to_timedelta(obj_str):
    """Turn an object string of the format X unit ago into timedelta."""
    value, unit, check = obj_str.split()
    assert check in ('after', 'ago')
    return timedelta(**{unit: float(value)})


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


def main(*argv):
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
    if not argv:  # pragma: no cover
        argv = sys_argv[1:]
    args = parser.parse_args(argv)
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


def cmd(*argv):
    """Main admin command line tool."""
    parser = ArgumentParser(description='Cart admin tool.')
    parser.add_argument(
        '-c', '--config', metavar='CONFIG', type=str, default=CONFIG_FILE,
        dest='config', help='cart config file'
    )
    parser.set_defaults(func=lambda _args: parser.print_help())
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
    fixit_parser = subparsers.add_parser(
        'fixit',
        description='Fix an existing cart'
    )
    fixit_parser.add_argument(
        '--cartid', dest='cartids', nargs='+', default=set(),
        help='Cart IDs to try and fix'
    )
    fixit_parser.set_defaults(func=fixit)
    dump_parser = subparsers.add_parser(
        'dump',
        description='Dump all the carts as yaml'
    )
    dump_parser.add_argument(
        '--json', default=False, action='store_true',
        help='Dump as Json'
    )
    dump_parser.set_defaults(func=dump)
    purge_parser = subparsers.add_parser(
        'purge',
        description='delete all carts before a time'
    )
    purge_parser.add_argument(
        '--time-ago', dest='time_ago', type=objstr_to_timedelta,
        help='only cart older than X days ago (i.e. --time-ago="7 days ago").',
        required=False, default=timedelta(days=180)
    )
    purge_parser.set_defaults(func=purge)
    if not argv:  # pragma: no cover
        argv = sys_argv[1:]
    args = parser.parse_args(argv)
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
        return bool2cmdint(OrmSync.create_tables())
    return bool2cmdint(OrmSync.update_tables())


def dump(args):
    """Dump the cart database."""
    tree = []
    carts = Cartutils.get_active_carts()
    for cart in carts:
        cdb = cart.dict()
        files = File.select().where(File.cart == cart)
        if files:
            cdb['files'] = []
            for c_file in files:
                cdb['files'].append(c_file.dict())
        tree.append(cdb)
    if args.json:
        print(json.dumps(tree))
    else:
        print(yaml.dump(tree))
    return 0


def purge(args):
    """purge old carts."""
    cart_utils = Cartutils()
    carts = cart_utils.get_active_carts()
    for cart in carts:
        if cart.updated_date < datetime.today() - args.time_ago:
            print('deleting:'+str(cart.dict()))
            message = cart_utils.remove_cart(cart.cart_uid, CART_APP.control.revoke)
            print(message)
    return 0
