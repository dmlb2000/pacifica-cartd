#!/bin/bash

export CART_CPCONFIG="server.conf"
python -c 'from pacifica.cart.orm import database_setup; database_setup()'
coverage run --include='pacifica/*' -p -m celery -A pacifica.cart.tasks worker -l info -P solo -c 1 &
CELERY_PID=$!
coverage run --include='pacifica/*' -p -m pacifica.cart --stop-after-a-moment &
SERVER_PID=$!
sleep 1
coverage run --include='pacifica/*' -a -m pytest pacifica/cart/test/cart_end_to_end_tests.py -xv
celery -A pacifica.cart.tasks control shutdown || true
wait $SERVER_PID $CELERY_PID
coverage combine -a .coverage*
coverage report -m --fail-under 100
if [[ $CODECLIMATE_REPO_TOKEN ]] ; then
  codeclimate-test-reporter
fi
