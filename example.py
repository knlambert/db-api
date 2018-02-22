# coding: utf-8
"""
Helper code.
"""
from flask import Flask
from sqlcollectionapi.api import Api
from sqlcollectionapi.db_api_blueprint import FlaskRestDBApi
from sqlcollection.client import Client
import MySQLdb


db = Client(
    host=u"127.0.0.1",
    user=u"root",
    password=u"localroot1234"
).hours_count

APP = Flask(__name__)

DB_REST_API_CONFIG = {
    u"projects": Api(db, default_table_name=u"project"),
    u"clients": Api(db, default_table_name=u"client"),
    u"hours": Api(db, default_table_name=u"hour"),
    u"project_assignements": Api(db, default_table_name=u"project_assignement"),
    u"users": Api(db, default_table_name=u"user"),
    u"cras": Api(db, default_table_name=u"cra")
}

DB_FLASK_API = FlaskRestDBApi(DB_REST_API_CONFIG)
DB_FLASK_API_BLUEPRINT = DB_FLASK_API.construct_blueprint()

APP.register_blueprint(DB_FLASK_API_BLUEPRINT, url_prefix=u'/api')

if __name__ == u"__main__":
    APP.run(debug=True)