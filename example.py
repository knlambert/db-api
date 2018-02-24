# coding: utf-8
"""
Helper code.
"""
from flask import Flask
from dbapi.dbapi import DBApi

from sqlcollection.client import Client
from user_api.user_api import UserApi
from dbapi.dbapi import DBApi

client = Client(url=u'mysql://root:localroot1234@127.0.0.1/')
db = client.hours_count

# Create user api object
user_api = UserApi(
    db_host=u"127.0.0.1",
    db_user=u"root",
    db_passwd=u"localroot1234",
    db_name=u"user_api",
    jwt_secret=u"DUMMY",
    jwt_lifetime=30 * 24 * 3600
)
flask_user_api = user_api.get_flask_adapter()

APP = Flask(__name__)
APP.register_blueprint(DBApi(db.hour).get_flask_adapter(flask_user_api).construct_blueprint(), url_prefix=u'/api/hours')
APP.register_blueprint(flask_user_api.construct_blueprint(), url_prefix=u"/api/users")
if __name__ == u"__main__":
    APP.run(debug=True)