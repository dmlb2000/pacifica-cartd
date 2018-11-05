#!/bin/bash -xe
mkdir ~/.pacifica-cartd
touch ~/.pacifica-cartd/config.ini
pip install requests eventlet
if [ "$RUN_LINTS" = "true" ]; then
  pip install pre-commit
else
  mysql -e 'CREATE DATABASE pacifica_cart;'
  pip install -e git://github.com/pacifica/pacifica-archiveinterface.git#egg=PacificaArchiveInterface
  pushd travis
  ArchiveInterfaceServer.py --config config.cfg &
  popd
  sleep 3
  python travis/archiveinterfacepreload.py
  pip install codeclimate-test-reporter
fi
