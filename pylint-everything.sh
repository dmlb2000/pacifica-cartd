#!/bin/bash -xe

pylint --extension-pkg-whitelist=pycurl cart
pylint cartserver
python -m cart.cart_unit_tests -v
