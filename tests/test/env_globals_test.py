#!/usr/bin/python
# -*- coding: utf-8 -*-
"""File used to unit test the pacifica_cart."""
import unittest
import os
import sys


class TestEnvGlobals(unittest.TestCase):
    """Contain the tests for the global config module."""

    def test_set_logging(self):
        """Test that logging gets set for debugging."""
        os.environ['DATABASE_LOGGING'] = 'True'
        import importlib
        # first delete the module from the loaded modules
        del sys.modules['pacifica.cartd.globals']
        # then we import the module
        mod = importlib.import_module('pacifica.cartd.globals')
        # make sure the LOGGER attribute in the module exists
        self.assertTrue(getattr(mod, 'CHERRYPY_CONFIG'))
