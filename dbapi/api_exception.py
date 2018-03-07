# coding: utf-8
"""
File contains base API Exception.
"""


class ApiException(Exception):

    def __init__(self, message, status_code=None, api_error_code=None, payload=None):
        Exception.__init__(self)
        self.message = message
        self.status_code = status_code if status_code else 400
        self.api_error_code = api_error_code or status_code
        self.payload = payload

    def to_dict(self):
        rv = dict(self.payload or ())
        rv[u'message'] = self.message
        return rv


class ApiNotFound(ApiException):

    def __init__(self, message, api_error_code=None, payload=None):
        ApiException.__init__(self, message, 404, api_error_code, payload)


class ApiUnprocessableEntity(ApiException):
    def __init__(self, message=u"Unprocessable Entity.", api_error_code=None, payload=None):
        ApiException.__init__(self, message, 422, api_error_code, payload)


class ApiForbidden(ApiException):
    def __init__(self, message=u"Forbidden.", api_error_code=None, payload=None):
        ApiException.__init__(self, message, 403, api_error_code, payload)


class ApiRoleMissing(ApiForbidden):
    def __init__(self):
        ApiForbidden.__init__(self, message=u"Forbidden. Role(s) missing.", api_error_code=u"ROLE_MISSING")


class ApiUnauthorized(ApiException):
    def __init__(self, message=u"Unauthorized.", api_error_code=None, payload=None):
        ApiException.__init__(self, message, 401, api_error_code, payload)


class ApiConflict(ApiException):
    def __init__(self, message=u"Conflict.", api_error_code=None, payload=None):
        ApiException.__init__(self, message, 409, api_error_code, payload)