#!/usr/bin/python
# -*- coding: utf-8 -*-
# pylint: disable=invalid-name
"""Run the Cart Server."""
import cherrypy
from cart.__main__ import main, error_page_default
from cart.cart_interface import CartRoot
from cart.cart_env_globals import CHERRYPY_CONFIG

cherrypy.config.update({'error_page.default': error_page_default})
# pylint doesn't realize that application is actually a callable
# pylint: disable=invalid-name
application = cherrypy.Application(CartRoot(), '/', CHERRYPY_CONFIG)
# pylint: enable=invalid-name

if __name__ == '__main__':
    main()
