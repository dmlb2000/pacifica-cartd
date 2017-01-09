#!/usr/bin/python
"""
Run all the unit tests in one script
"""
import unittest

from cart.test.cart_interface_tests import TestCartInterface
from cart.test.cart_utils_tests import TestCartUtils
from cart.test.env_globals_tests import TestEnvGlobals
from cart.test.archive_unit_tests import TestArchiveRequests
from cart.test.cart_tasks_tests import TestCartTasks
from cart.test.cart_orm_tests import TestCartOrm

unittest.main()
