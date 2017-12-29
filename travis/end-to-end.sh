#!/bin/bash
export MYSQL_ENV_MYSQL_PASSWORD=
export MYSQL_ENV_MYSQL_USER=travis
coverage run --include='cart/*' -p -m celery -A cart worker -l info &
CELERY_PID=$!
coverage run --include='cart/*' -p -m cart --stop-after-a-moment &
SERVER_PID=$!
sleep 1
coverage run --include='cart/*' -a -m pytest cart/test/cart_end_to_end_tests.py -v
sleep 4
celery -A cart control shutdown || true
wait $SERVER_PID $CELERY_PID
coverage combine -a .coverage*
coverage report -m --fail-under 100
if [[ $CODECLIMATE_REPO_TOKEN ]] ; then
  codeclimate-test-reporter
fi
