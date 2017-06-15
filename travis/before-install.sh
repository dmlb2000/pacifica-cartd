#!/bin/bash -xe
pip install requests
if [ "$RUN_LINTS" = "true" ]; then
  pip install pre-commit
else
  mysql -e 'CREATE DATABASE pacifica_cart;'
  pip install -e git://github.com/pacifica/pacifica-archiveinterface.git#egg=PacificaArchiveInterface
  archiveinterfaceserver.py --config travis/config.cfg &
  sleep 3
  python travis/archiveinterfacepreload.py
  pip install codeclimate-test-reporter coverage nose pytest
fi
