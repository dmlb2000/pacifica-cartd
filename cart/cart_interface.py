#!/usr/bin/python
"""Class for the cart interface.  Allows API to file interactions"""
from json import dumps
from os import path
from sys import stderr
import doctest
import cart.cart_interface_responses as cart_interface_responses

class CartInterfaceError(Exception):
    """
    CartInterfaceError - basic exception class for this module.
    Will be used to throw exceptions up to the top level of the application
    >>> CartInterfaceError()
    CartInterfaceError()
    """
    pass

class CartGenerator(object):
    """Defines the methods that can be used for cart request types
    doctest for the cart generator class
    HPSS Doc Tests
    """
    def __init__(self):
        self._response = None

    def get(self, env, start_response):
        """Download the tar file created by the cart"""
        resp = cart_interface_responses.Responses()
        self._response = resp.base_response(start_response)
        return self.return_response()

    def status(self, env, start_response):
        """Get the status of a carts tar file"""
        resp = cart_interface_responses.Responses()
        self._response = resp.base_response(start_response)
        return self.return_response()

    def stage(self, env, start_response):
        """Tell the archive interface to stage all the files"""
        resp = cart_interface_responses.Responses(start_response)
        self._response = resp.base_response()
        return self.return_response()

    def return_response(self):
        """Prints all responses in a nice fashion"""
        return dumps(self._response, sort_keys=True, indent=4)


    def pacifica_cartinterface(self, env, start_response):
        """Parses request method type"""
        try:
            if env['REQUEST_METHOD'] == 'GET':
                return self.get(env, start_response)
            elif env['REQUEST_METHOD'] == 'HEAD':
                return self.status(env, start_response)
            elif env['REQUEST_METHOD'] == 'POST':
                return self.stage(env, start_response)
            else:
                resp = cart_interface_responses.Responses()
                self._response = resp.unknown_request(start_response,
                                                      env['REQUEST_METHOD'])
            return self.return_response()
        except CartInterfaceError:
            #catching application errors
            #all exceptions set the return response
            #if the response is not set, set it as unknown
            if self._response is None:
                resp = cart_interface_responses.Responses()
                self._response = resp.unknown_exception(start_response)
            return self.return_response()


if __name__ == "__main__":
    doctest.testmod(verbose=True)