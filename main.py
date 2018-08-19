# coding: utf-8
"""
Helper code.
"""
import user_api
from flask import Flask
from sqlcollection.client import Client
from dbapi.dbapi import DBApi

client = Client(url=u'mysql+mysqlconnector://root:localroot1234@127.0.0.1/')

# Create user api object
USER_API = user_api.create_user_api(
    db_url=u"mysql+mysqlconnector://root:localroot1234@127.0.0.1/user_api",
    jwt_secret=u"dummy_secret",
    jwt_lifetime=30 * 24 * 3600
)

flask_user_api = USER_API.get_flask_user_api()


FLASK_USER_API = USER_API.get_flask_user_api()

APP = Flask(__name__)


# Register the blueprint
APP.register_blueprint(flask_user_api.construct_user_api_blueprint(), url_prefix=u"/api/users")
APP.register_blueprint(flask_user_api.construct_role_api_blueprint(), url_prefix=u"/api/roles")

DB_API_CONFIG = {
    u"users": DBApi(client, u"_user", database_name="user_api")
}

for service_name, db_api in list(DB_API_CONFIG.items()):
    db_blueprint = db_api.get_flask_adapter(FLASK_USER_API).construct_blueprint()

    FLASK_USER_API.add_api_error_handler(db_blueprint)

    @db_blueprint.before_request
    @FLASK_USER_API.is_connected(login_url=u"/login")
    def is_connected():
        pass

    APP.register_blueprint(
        db_blueprint,
        url_prefix=u'/api/db/{}'.format(service_name)
    )

if __name__ == u"__main__":
    APP.run(debug=True)