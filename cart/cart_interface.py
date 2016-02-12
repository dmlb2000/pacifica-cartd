#!/usr/bin/python
"""Class for the cart interface.  Allows API to file interactions"""
import json
from os import path
from sys import stderr
import doctest
import cart.cart_interface_responses as cart_interface_responses
from cart.tasks import stageFiles, cartStatus, availableCart, remove_cart


BLOCK_SIZE = 1<<20

class CartInterfaceError(Exception):
    """
    CartInterfaceError - basic exception class for this module.
    Will be used to throw exceptions up to the top level of the application
    >>> CartInterfaceError()
    CartInterfaceError()
    """
    pass

def fix_cart_uid(uid):
    """Removes / from front of cart_uid"""
    if path.isabs(uid):
        uid = uid[1:]
    return uid

def is_valid_uid(uid):
    """checks to see if the uid is valid before using it"""
    if not uid:
        return False
    if uid == "":
        return False

    return True


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
        uid = fix_cart_uid(env['PATH_INFO'])
        is_valid = is_valid_uid(uid)
        if not is_valid:
            self._response = resp.invalid_uid_error_response(
                start_response, uid)
            return self.return_response()
        #get the bundle path if available
        cart_path = availableCart(uid)
        if cart_path == False:
            #cart not ready
            self._response = resp.unready_cart(start_response)
            return self.return_response()
        else:
            if path.isfile(cart_path):
                #give back bundle here
                stderr.flush()
                try:
                    myfile = open(cart_path, "r")
                    start_response('200 OK', [('Content-Type',
                                               'application/octet-stream')])
                    if 'wsgi.file_wrapper' in env:
                        return env['wsgi.file_wrapper'](myfile, BLOCK_SIZE)
                    return iter(lambda: myfile.read(BLOCK_SIZE), '')
                except IOError:
                    self._response = resp.bundle_doesnt_exist(start_response)
            else:
                self._response = resp.bundle_doesnt_exist(start_response)
                return self.return_response()


        return self.return_response()

    def status(self, env, start_response):
        """Get the status of a carts tar file"""
        resp = cart_interface_responses.Responses()
        uid = fix_cart_uid(env['PATH_INFO'])
        is_valid = is_valid_uid(uid)
        if not is_valid:
            self._response = resp.invalid_uid_error_response(
                start_response, uid)
            return self.return_response()

        status = cartStatus(uid)
        self._response = resp.cart_status_response(start_response, status)
        return self.return_response()

    def stage(self, env, start_response):
        """Get all the files locally and bundled"""
        resp = cart_interface_responses.Responses()
        try:
            request_body_size = int(env.get('CONTENT_LENGTH', 0))
        except ValueError:
            request_body_size = 0

        try:
            request_body = env['wsgi.input'].read(request_body_size)
            data = json.loads(request_body)
            file_ids = data['fileids']
        except IOError:
            # is exception is probably from the read()
            self._response = resp.json_stage_error_response(start_response)
            return self.return_response()
        except ValueError:
            self._response = resp.json_stage_error_response(start_response)
            return self.return_response()

        uid = fix_cart_uid(env['PATH_INFO'])
        is_valid = is_valid_uid(uid)
        if not is_valid:
            self._response = resp.invalid_uid_error_response(
                start_response, uid)
            return self.return_response()

        stageFiles.delay(file_ids, uid)
        self._response = resp.cart_proccessing_response(start_response)
        return self.return_response()

    def delete_cart(self, env, start_response):
        """Delete a cart that has been created"""
        resp = cart_interface_responses.Responses()
        uid = fix_cart_uid(env['PATH_INFO'])
        is_valid = is_valid_uid(uid)
        if not is_valid:
            self._response = resp.invalid_uid_error_response(
                start_response, uid)
            return self.return_response()

        message = remove_cart(uid)
        self._response = resp.cart_delete_response(start_response, message)
        return self.return_response()

    def return_response(self):
        """Prints all responses in a nice fashion"""
        return json.dumps(self._response, sort_keys=True, indent=4)


    def pacifica_cartinterface(self, env, start_response):
        """Parses request method type"""
        try:
            if env['REQUEST_METHOD'] == 'GET':
                return self.get(env, start_response)
            elif env['REQUEST_METHOD'] == 'HEAD':
                return self.status(env, start_response)
            elif env['REQUEST_METHOD'] == 'POST':
                return self.stage(env, start_response)
            elif env['REQUEST_METHOD'] == 'DELETE':
                return self.delete_cart(env, start_response)
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
