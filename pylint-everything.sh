#!/bin/bash -xe

pylint --extension-pkg-whitelist=pycurl cart
pylint cartserver
