# Development

There are pre-existing services that the testing suite requires to
run. Without those running services the test suite will fail.

## Pre-requisites
 * create a virtual environment and load the python packages with pip
```
pip install -r requirements-dev.txt
```
 * start a docker archive interface:
```
docker run --rm -p 8080:8080 pacifica/archiveinterface
```
 * start a redis interface(check this)
```
docker run --rm -p 6379:6379 redis
```

## Run the tests
```
coverage run --include 'pacifica/cartd/*' -m pytest -xsv tests/test tests/e2e
```
