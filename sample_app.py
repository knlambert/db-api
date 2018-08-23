# coding: utf-8
"""
Helper code.
"""
from flask import Flask
from sqlcollection.client import Client
from user_api import create_user_api
from dbapi.dbapi import DBApi

user_api = create_user_api(
    db_url=u"postgresql://postgres:postgresql@127.0.0.1/user_api",
    jwt_secret=u"dummy_secret"
)


client = Client(url=u'postgresql+psycopg2://postgres:postgresql@127.0.0.1:5432')

APP = Flask(__name__)

DB_API_CONFIG = {
    u"projects": DBApi(client, u"project", prefix="app_tenant_"),
    u"clients": DBApi(client, u"client", prefix="app_tenant_")
}

flask_user_api = user_api.get_flask_user_api()
# Register the blueprint
APP.register_blueprint(flask_user_api.construct_user_api_blueprint(), url_prefix=u"/api/users")
APP.register_blueprint(flask_user_api.construct_role_api_blueprint(), url_prefix=u"/api/roles")

for service_name, db_api in list(DB_API_CONFIG.items()):
    db_blueprint = db_api.get_flask_adapter(
        flask_user_api).construct_blueprint()

    APP.register_blueprint(
        db_blueprint,
        url_prefix=u'/api/db/{}'.format(service_name)
    )

if __name__ == u"__main__":
    APP.run(debug=True)
