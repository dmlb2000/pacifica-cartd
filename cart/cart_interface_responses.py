"""File for setting up Cart Interface server responses."""


class Responses(object):
    """Basic responses class to centralize how we reply to given states."""

    def unknown_request(self, start_response, request_method):
        """Response for when unknown request type given."""
        start_response('501 Not Implemented', [('Content-Type', 'application/json')])
        self._response = {
            'message': 'Unknown request method',
            'request_method': request_method
        }
        return self._response

    def cart_proccessing_response(self, start_response):
        """Response base."""
        start_response('201 Created', [('Content-Type', 'application/json')])
        self._response = {
            'message': 'Cart Processing has begun'
        }
        return self._response

    def json_stage_error_response(self, start_response):
        """Response for when there is a problem reading the json file."""
        start_response('400 Bad Request', [('Content-Type', 'application/json')])
        self._response = {
            'message': 'JSON content could not be read'
        }
        return self._response

    def unready_cart(self, start_response):
        """Response for when the cart is not ready for download."""
        start_response('202 Accepted', [('Content-Type', 'application/json')])
        self._response = {
            'message': 'The cart is not ready for download'
        }
        return self._response

    def bundle_doesnt_exist(self, start_response):
        """Response for when the cart bundle does not exist."""
        start_response('404 Not Found', [('Content-Type', 'application/json')])
        self._response = {
            'message': 'The cart bundle does not exist'
        }
        return self._response

    def unknown_exception(self, start_response):
        """Response when unknown exception occurs."""
        start_response('500 Internal Server Error', [('Content-Type', 'application/json')])
        self._response = {
            'message': 'Unknown Exception Occured'
        }
        return self._response

    def invalid_uid_error_response(self, start_response, uid):
        """Response when invalid uid is sent."""
        start_response('400 Bad Request', [('Content-Type', 'application/json')])
        self._response = {
            'message': 'The uid was not valid',
            'uid': uid
        }
        return self._response

    def cart_status_response(self, start_response, status):
        """
        Response that tells the carts status.

        Status is a tuple of status, and message.
        """
        self._response = ''
        response_headers = [
            ('X-Pacifica-Status', str(status[0])),
            ('X-Pacifica-Message', str(status[1])),
            ('Content-Type', 'application/json')
        ]

        if str(status[0]) == 'error':
            # need to see if resource no longer exists and throw a 404 then
            no_cart = 'No cart with uid'
            no_cart_length = len(no_cart)
            error_sub = status[1][:no_cart_length]
            if error_sub == no_cart:
                start_response('404 Not Found', response_headers)
            else:
                start_response('500 Internal Server Error', response_headers)
        else:
            start_response('204 No Content', response_headers)
        return self._response

    def test_response(self, start_response, variable):  # pragma: no cover
        """Test response."""
        start_response('200 OK', [('Content-Type', 'application/json')])
        self._response = {
            'message': variable
        }
        return self._response

    def cart_not_found(self, start_response):  # pragma: no cover
        """Test response."""
        start_response('404 Not Found', [('Content-Type', 'application/json')])
        self._response = {
            'message': 'The cart does not exist or has already been deleted'
        }
        return self._response

    def cart_delete_response(self, start_response, message):
        """Response For cart deletion."""
        start_response('200 OK', [('Content-Type', 'application/json')])
        self._response = {
            'message': str(message)
        }
        return self._response

    def __init__(self):
        """Constructor to set internal variables."""
        self._response = None
