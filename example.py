# coding: utf-8
"""
Helper code.
"""
import user_api
from flask import Flask
from sqlcollection.client import Client
from dbapi.dbapi import DBApi

client = Client(url=u'mysql://root:localroot1234@127.0.0.1/')
DB = client.hours_count

# Create user api object
USER_API = user_api.create_user_api(
    db_url=u"mysql://root:localroot1234@127.0.0.1/user_api",
    jwt_secret=u"DUMMY",
    jwt_lifetime=30 * 24 * 3600
)

FLASK_USER_API = USER_API.get_flask_user_api()

APP = Flask(__name__)

DB_API_CONFIG = {
    u"projects": DBApi(DB, u"project"),
    u"clients": DBApi(DB, u"client"),
    u"hours": DBApi(DB, u"hour")
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