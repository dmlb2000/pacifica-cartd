#!/bin/bash
if [[ -z $PEEWEE_DATABASE_URL ]] ; then
  if [[ $PEEWEE_USER && $PEEWEE_PASS ]]; then
    PEEWEE_USER_PART="${PEEWEE_USER}:${PEEWEE_PASS}@"
  fi
  if [[ $PEEWEE_PORT ]] ; then
    PEEWEE_ADDR_PART="${PEEWEE_ADDR}:${PEEWEE_PORT}"
  else
    PEEWEE_ADDR_PART=$PEEWEE_ADDR
  fi
  PEEWEE_DATABASE_URL="${PEEWEE_PROTO}://${PEEWEE_USER_PART}${PEEWEE_ADDR_PART}/${PEEWEE_DATABASE}"
fi
mkdir ~/.pacifica-cartd/
printf '[database]\npeewee_url = '${PEEWEE_DATABASE_URL}'\n' > ~/.pacifica-cartd/config.ini
python -c 'from pacifica.cartd.__main__ import cmd; cmd()' dbsync
uwsgi \
  --http-socket 0.0.0.0:8081 \
  --master \
  --die-on-term \
  --wsgi-file /usr/src/app/pacifica/cartd/wsgi.py "$@"
