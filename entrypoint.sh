#!/bin/bash
uwsgi \
  --http-socket 0.0.0.0:8081 \
  --master \
  --die-on-term \
  --wsgi-file /usr/src/app/CartServer.py "$@"
