# coding: utf-8


from .flask_utils import (
    AUTO_LOOKUP_SCHEMA,
    flask_construct_response,
    LIST_API_VALIDATION_SCHEMA,
    flask_constructor_error,
    flask_check_and_inject_args,
    flask_check_and_inject_payload,
    UPDATE_API_VALIDATION_SCHEMA,
    DELETE_API_VALIDATION_SCHEMA
)
from ..api_exception import ApiException
from flask import Blueprint, make_response


class FlaskAdapter(object):

    def __init__(self, db_api, flask_user_api):
        """
        Constructor.
        Args:
            db_api (DBApi): The database api to use.
            flask_user_api: The user api to apply for security purpose.
        """
        self._db_api = db_api
        self._flask_user_api = flask_user_api

        self._db_api_blueprint = None

    def construct_blueprint(self):
        """
        Constructs a blueprint wrapping the DBApi.
        Returns:
            (Blueprint): The constructed blueprint.
        """
        self._db_api_blueprint = Blueprint(u'{}_db_api'.format(
            self._db_api._table_name
        ), __name__)

        @self._db_api_blueprint.route(u'/', methods=[u"GET"])
        @self._flask_user_api.is_connected(inject_token=True)
        @flask_check_and_inject_args(LIST_API_VALIDATION_SCHEMA)
        def find(args, token):
            args[u"database_name"] = str(token["customer"]["id"])
            return flask_construct_response(
                self._db_api.list(**args),
                200
            )

        @self._db_api_blueprint.route(u'/', methods=[u"POST"])
        @self._flask_user_api.is_connected(inject_token=True)
        @flask_check_and_inject_args(AUTO_LOOKUP_SCHEMA)
        @flask_check_and_inject_payload()
        def create(args, payload, token):
            args[u"database_name"] = str(token["customer"]["id"])
            args[u"document"] = payload
            return flask_construct_response(
                self._db_api.create(**args),
                code=201
            )

        @self._db_api_blueprint.route(u'/', methods=[u"PUT"])
        @self._flask_user_api.is_connected(inject_token=True)
        @flask_check_and_inject_args(UPDATE_API_VALIDATION_SCHEMA)
        @flask_check_and_inject_payload()
        def update(args, payload, token):
            args[u"update"] = payload
            args[u"database_name"] = str(token["customer"]["id"])
            return flask_construct_response(
                self._db_api.update(**args),
                code=200
            )

        @self._db_api_blueprint.route(u'/', methods=[u"DELETE"])
        @self._flask_user_api.is_connected(inject_token=True)
        @flask_check_and_inject_args(DELETE_API_VALIDATION_SCHEMA)
        def delete(args, token):
            args[u"database_name"] = str(token["customer"]["id"])
            return flask_construct_response(
                self._db_api.delete(**args),
                code=202
            )

        @self._db_api_blueprint.route(u'/description', methods=[u"GET"])
        @self._flask_user_api.is_connected(inject_token=True)
        @flask_check_and_inject_args(AUTO_LOOKUP_SCHEMA)
        def description(args, token):
            args[u"database_name"] = str(token["customer"]["id"])
            return flask_construct_response(
                self._db_api.description(**args),
                code=200
            )

        @self._db_api_blueprint.route(u'/export', methods=[u"GET"])
        @self._flask_user_api.is_connected(inject_token=True)
        @flask_check_and_inject_args(LIST_API_VALIDATION_SCHEMA)
        def export(args, token):
            args[u"database_name"] = str(token["customer"]["id"])
            output = make_response(self._db_api.export(**args))
            output.headers[U"Content-Disposition"] = "attachment; "\
                "filename=export.csv"
            output.headers[U"Content-type"] = U"text/csv"
            return output, 200

        @self._db_api_blueprint.errorhandler(ApiException)
        def api_error_handler(exception):
            return flask_constructor_error(
                exception.message,
                exception.status_code,
                custom_error_code=exception.api_error_code,
                error_payload=exception.payload
            )

        return self._db_api_blueprint
