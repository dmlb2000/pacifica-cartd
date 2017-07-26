#!/bin/bash
pre-commit run -a
pylint --rcfile=pylintrc cart
pylint --rcfile=pylintrc CartServer DatabaseCreate setup.py
radon cc cart CartServer DatabaseCreate setup.py
