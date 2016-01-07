#!/usr/bin/python
"""
Pacifica Cart Interface
This is the main program that starts the WSGI server.
The core of the server code is in cart_interface.py.
"""
from argparse import ArgumentParser
from wsgiref.simple_server import make_server
#from cart.tasks import write_message
from cart.cart_interface import CartGenerator

PARSER = ArgumentParser(description='Run the cart interface.')

PARSER.add_argument('-p', '--port', metavar='PORT', type=int,
                    default=8080, dest='port',
                    help="port to listen on")
PARSER.add_argument('-a', '--address', metavar='ADDRESS',
                    default='localhost', dest='address',
                    help="address to listen on")

ARGS = PARSER.parse_args()
GENERATOR = CartGenerator()
SRV = make_server(ARGS.address, ARGS.port,
                  GENERATOR.pacifica_cartinterface)

SRV.serve_forever()