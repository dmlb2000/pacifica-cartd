#!/bin/bash -xe

pylint --extension-pkg-whitelist=pycurl cart
pylint cartserver
coverage run --include='cart/*' -m cart.cart_unit_tests -v
coverage report -m
