# coding: utf-8


from .flask_utils import (
    flask_check_and_inject_payload,
    flask_construct_response,
    flask_check_and_inject_args,
    LIST_API_VALIDATION_SCHEMA
)
from flask import Blueprint


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

    def construct_blueprint(self):
        """
        Constructs a blueprint wrapping the DBApi.
        Returns:
            (Blueprint): The constructed blueprint.
        """
        db_api_blueprint = Blueprint(u'{}_db_api'.format(self._db_api._db._table.name), __name__)

        @db_api_blueprint.route(u'/', methods=[u"GET"])
        @self._flask_user_api.is_connected()
        @flask_check_and_inject_args(LIST_API_VALIDATION_SCHEMA)
        def find(args):
            print(args)
            return flask_construct_response(
                self._db_api.list(**args),
                200
            )

        return db_api_blueprint