#!/usr/bin/python
"""
Run all the unit tests in one script
"""
import unittest

from cart.cart_unit_tests import TestCartUtils, TestCartInterface
from cart.archive_unit_tests import TestArchiveRequests

unittest.main()
