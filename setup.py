#!/usr/bin/python
"""Setup and install the cart."""
from setuptools import setup

setup(name='PacificaCartd',
      version='1.0',
      description='Pacifica Cartd',
      author='David Brown',
      author_email='david.brown@pnnl.gov',
      packages=['cart'],
      scripts=['CartServer.py', 'DatabaseCreate.py'])
