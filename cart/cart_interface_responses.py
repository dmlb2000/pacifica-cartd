"""File for setting up Cart Interface server responses"""
class Responses(object):

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

    def unknown_exception(self, start_response):
        """Response when unknown exception occurs"""
        start_response('200 OK', [('Content-Type', 'application/json')])
        self._response = {
            'message': 'Unknown Exception Occured'
        }
        return self._response


    def __init__(self):
        self._response = None