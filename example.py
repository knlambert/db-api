# coding: utf-8
"""
Helper code.
"""
import user_api
from flask import Flask
from sqlcollection.client import Client
from dbapi.dbapi import DBApi

client = Client(url=u'mysql://root:localroot1234@127.0.0.1/')
db = client.hours_count

# Create user api object
USER_API = user_api.UserApi(
    db_host=u"127.0.0.1",
    db_user=u"root",
    db_passwd=u"localroot1234",
    db_name=u"user_api",
    jwt_secret=u"DUMMY",
    jwt_lifetime=30 * 24 * 3600
)
flask_user_api = USER_API.get_flask_adapter()


APP = Flask(__name__)
APP.register_blueprint(flask_user_api.construct_blueprint(), url_prefix=u"/api/users")

services = [
    (u"hour", u"hours")
]

for table_name, service_name in services:

    db_blueprint = DBApi(db, table_name).get_flask_adapter(flask_user_api).construct_blueprint()

    @db_blueprint.errorhandler(user_api.ApiException)
    def user_api_error_wrapper(exception):
        return flask_user_api.api_error_handler(exception)


    APP.register_blueprint(
        db_blueprint,
        url_prefix=u'/api/{}'.format(service_name)
    )


if __name__ == u"__main__":
    APP.run(debug=True)