#!/bin/bash
coverage run --include='cart/*' test.py -v
codeclimate-test-reporter
