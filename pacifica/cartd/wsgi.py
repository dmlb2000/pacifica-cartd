#!/usr/bin/python
# -*- coding: utf-8 -*-
# pylint: disable=invalid-name
"""Run the Cart Server."""
import cherrypy
from .rest import CartRoot, error_page_default
from .globals import CHERRYPY_CONFIG

cherrypy.config.update({'error_page.default': error_page_default})
# pylint doesn't realize that application is actually a callable
# pylint: disable=invalid-name
application = cherrypy.Application(CartRoot(), '/', CHERRYPY_CONFIG)
# pylint: enable=invalid-name
