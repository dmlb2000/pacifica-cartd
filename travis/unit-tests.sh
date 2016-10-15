#!/bin/bash
coverage run --include='cart/*' test.py -v
coverage report -m
codeclimate-test-reporter
