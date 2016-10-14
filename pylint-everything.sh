#!/bin/bash -xe

pylint cart
pylint cartserver
coverage run --include='cart/*' -m cart.cart_unit_tests -v
coverage report -m
