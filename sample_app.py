# coding: utf-8
"""
Helper code.
"""
from flask import Flask
from sqlcollection.client import Client
from dbapi.dbapi import DBApi

client = Client(url=u'mysql+mysqlconnector://root:localroot1234@127.0.0.1/')

APP = Flask(__name__)

DB_API_CONFIG = {
    u"projects": DBApi(client, u"project", database_name="toolbox_1"),
    u"clients": DBApi(client, u"client", database_name="toolbox_1")
}

for service_name, db_api in list(DB_API_CONFIG.items()):
    db_blueprint = db_api.get_flask_adapter(None).construct_blueprint()

    APP.register_blueprint(
        db_blueprint,
        url_prefix=u'/api/db/{}'.format(service_name)
    )

if __name__ == u"__main__":
    APP.run(debug=True)