"""File for setting up Cart Interface server responses"""
class Responses(object):
    """
    Basic responses class to centralize how we reply to given states.
    """
    def unknown_request(self, start_response, request_method):
        """Response for when unknown request type given"""
        start_response('200 OK', [('Content-Type', 'application/json')])
        self._response = {
            'message': 'Unknown request method',
            'request_method': request_method
        }
        return self._response
    def base_response(self, start_response):
        """Response base"""
        start_response('200 OK', [('Content-Type', 'application/json')])
        self._response = {
            'message': 'Basic return'
        }
        return self._response

    def cart_proccessing_response(self, start_response):
        """Response base"""
        start_response('200 OK', [('Content-Type', 'application/json')])
        self._response = {
            'message': 'Cart Processing has begun'
        }
        return self._response

    def json_stage_error_response(self, start_response):
        """Response for when there is a problem reading the json file"""
        start_response('500 OK', [('Content-Type', 'application/json')])
        self._response = {
            'message': 'JSON content could not be read'
        }
        return self._response

    def unready_cart(self, start_response):
        """Response for when the cart is not ready for download"""
        start_response('500 OK', [('Content-Type', 'application/json')])
        self._response = {
            'message': 'The cart is not ready for download'
        }
        return self._response

    def bundle_doesnt_exist(self, start_response):
        """Response for when the cart bundle does not exist"""
        start_response('500 OK', [('Content-Type', 'application/json')])
        self._response = {
            'message': 'The cart bundle does not exist'
        }
        return self._response

    def unknown_exception(self, start_response):
        """Response when unknown exception occurs"""
        start_response('200 OK', [('Content-Type', 'application/json')])
        self._response = {
            'message': 'Unknown Exception Occured'
        }
        return self._response

    def invalid_uid_error_response(self, start_response, uid):
        """Response when unknown exception occurs"""
        start_response('200 OK', [('Content-Type', 'application/json')])
        self._response = {
            'message': "The uid was not valid",
            'uid': uid
        }
        return self._response

    def cart_status_response(self, start_response, status):
        """Response that tells the carts status.
           Status is a tuple of status, and message"""
        start_response('200 OK', [('Content-Type', 'application/json')])
        if status[1] != "":
            self._response = {
                'status': status[0],
                'message': status[1]
            }
        else:
            self._response = {
                'status': status[0]
            }
        return self._response

    def test_response(self, start_response, variable):
        """Response when unknown exception occurs"""
        start_response('200 OK', [('Content-Type', 'application/json')])
        self._response = {
            'message': variable
        }
        return self._response

    def cart_delete_response(self, start_response, message):
        """Response For cart deletion"""
        start_response('200 OK', [('Content-Type', 'application/json')])
        self._response = {
            'message': str(message)
        }
        return self._response

    def __init__(self):
        self._response = None
