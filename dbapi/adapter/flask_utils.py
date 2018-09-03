# coding: utf-8
"""
Blueprint utils methods
"""

import json
from functools import wraps
from cerberus import Validator
from flask import jsonify, request
from collections import OrderedDict


def flask_constructor_error(
    message: str, 
    status: int = 500, 
    custom_error_code: str = None,
    error_payload: dict = None
):
    """
    Construct Json Error returned message.
    """
    payload = {
        u"message": message
    }
    if error_payload:
        payload[u"payload"] = error_payload

    if custom_error_code:
        payload[u"error_code"] = custom_error_code

    return jsonify(payload), status


def flask_construct_response(item, code=200):
    """
    Construct Json response returned.
    """
    return jsonify(item), code


def to_dict(string: str):
    return json.loads(string, encoding="utf8")


def to_str_list(string: str):
    return string.split(",")


def to_int_list(string: str):
    return [int(val) for val in string.split(",")]


LIST_API_VALIDATION_SCHEMA = {
    u"projection": {
        u"type": u"dict",
        u"coerce": to_dict
    },
    u"offset": {
        u"type": u"integer",
        u"coerce": int
    },
    u"limit": {
        u"type": u"integer",
        u"coerce": int
    },
    u"order": {
        u"type": u"list",
        u"coerce": to_str_list
    },
    u"order_by": {
        u"type": u"list",
        u"coerce": to_int_list
    }
}
UPDATE_API_VALIDATION_SCHEMA = {}
DELETE_API_VALIDATION_SCHEMA = {}

FILTER_SCHEMA = {
    u"filter": {
        u"type": u"dict",
        u"coerce": to_dict
    }
}

FILTER_UPDATE_DELETE_SCHEMA = {
    u"filter": {
        u"type": u"dict",
        u"coerce": to_dict,
        u"required": True
    }
}

DEEP_UPDATE = {
    u"deep_update": {
        u"type": u"boolean",
        u"required": False,
        u"default": False,
        u"coerce": lambda x: str(x).lower() == u"true"
    }
}

AUTO_LOOKUP_SCHEMA = {
    u"lookup": {
        u'type': u'list',
        u"coerce": to_dict,
        u'schema': {
            u'type': u'dict',
            u'schema': {
                u"as": {
                    u"type": u"string",
                    u"required": True
                },
                u"from": {
                    u"type": u"string",
                    u"required": True
                },
                u"to": {
                    u"type": u"string",
                    u"required": True
                },
                u"localField": {
                    u"type": u"string",
                    u"required": True
                },
                u"foreignField": {
                    u"type": u"string",
                    u"required": True
                }
            }
        }
    },
    u"auto_lookup": {
        u"type": u"integer",
        u"coerce": int
    }
}

LIST_API_VALIDATION_SCHEMA.update(AUTO_LOOKUP_SCHEMA)
LIST_API_VALIDATION_SCHEMA.update(FILTER_SCHEMA)


UPDATE_API_VALIDATION_SCHEMA.update(DEEP_UPDATE)
UPDATE_API_VALIDATION_SCHEMA.update(AUTO_LOOKUP_SCHEMA)
UPDATE_API_VALIDATION_SCHEMA.update(FILTER_UPDATE_DELETE_SCHEMA)

DELETE_API_VALIDATION_SCHEMA.update(AUTO_LOOKUP_SCHEMA)
DELETE_API_VALIDATION_SCHEMA.update(FILTER_UPDATE_DELETE_SCHEMA)


LANGUAGE_SCHEMA = {
    u"lang": {
        u"type": u"string",
        u"required": True
    }
}


def flask_check_and_inject_args(validation_schema):
    """

    Args:
        validation_schema (dict):

    Returns:
        (funct):
    """

    def decorated(funct):
        @wraps(funct)
        def wrapper(*args, **kwargs):
            args_dict = request.args.copy().to_dict()

            validator = Validator(validation_schema)
            # Check if the document is valid.
            if not validator.validate(args_dict):
                return flask_constructor_error(
                    message=u"Wrong args.",
                    custom_error_code=u"WRONG_ARGS",
                    status=422,
                    error_payload=validator.errors
                )

            kwargs[u"args"] = validator.document
            return funct(*args, **kwargs)

        return wrapper

    return decorated


def flask_check_and_inject_payload(validation_schema=None):
    def decorated(funct):

        @wraps(funct)
        def wrapper(*args, **kwargs):

            if (
                request.headers.get(u"Content-Type") and 
                "application/json" in request.headers.get(u"Content-Type")
            ):
                try:
                    args_dict = json.loads(
                        request.data,
                        object_pairs_hook=OrderedDict,
                        encoding=u"utf8"
                    )
                except ValueError as err:
                    return flask_constructor_error(
                        message=str(err),
                        custom_error_code=u"WRONG_PAYLOAD",
                        status=422
                    )
                if validation_schema:
                    validator = Validator(validation_schema)

                    if not validator.validate(args_dict):
                        return flask_constructor_error(
                            message=u"Wrong args.",
                            custom_error_code=u"WRONG_ARGS",
                            status=422,
                            error_payload=validator.errors
                        )
                    args_dict = validator.document
                kwargs[u"payload"] = args_dict
                return funct(*args, **kwargs)
            else:
                return flask_constructor_error(
                    message=u"The payload format is unknown.",
                    custom_error_code=u"WRONG_PAYLOAD_FORMAT",
                    status=422
                )

        return wrapper

    return decorated
