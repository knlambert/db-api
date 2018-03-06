# coding utf-8

import datetime
from mock import Mock
from pytest import fixture
from dbapi.dbapi import DBApi


@fixture(scope=u"function")
def fake_db_api():
    return DBApi(Mock(), u"project")


@fixture(scope=u"function")
def project_description():
    return {
        u'fields': [
            {u'required': True, u'type': u'integer', u'name': u'id', u'primary_key': True},
            {u'required': True, u'type': u'string', u'name': u'name', u'primary_key': False}, {
                u'nested_description': {u'fields': [
                    {u'required': True, u'type': u'integer', u'name': u'id', u'primary_key': True},
                    {u'required': True, u'type': u'string', u'name': u'name', u'primary_key': False}],
                    u'as': u'client', u'table': u'client'}, u'required': True,
                u'type': u'integer', u'name': u'client', u'primary_key': False},
            {u'required': False, u'type': u'integer', u'name': u'provisioned_hours', u'primary_key': False},
            {u'required': True, u'type': u'datetime', u'name': u'started_at', u'primary_key': False},
            {u'required': False, u'type': u'string', u'name': u'code', u'primary_key': False}],
        u'as': u'project', u'table': u'project'}


def test__convert_python_types(fake_db_api):
    # Basic test, datetime.
    expected = {
        u"id": 1,
        u"name": u"My project",
        u"started_at": datetime.datetime(
            year=2018,
            month=3,
            day=4,
            hour=21,
            minute=27,
            second=32
        )
    }
    result = fake_db_api._convert_python_types([expected])
    assert [expected] == result
    assert result[0][u"started_at"] == 1520198852
    assert isinstance(result[0][u"started_at"], int)
    # With recursion, date
    expected[u"client"] = {
        u"id": 2,
        u"name": u"Awesome client.",
        u"creation": datetime.date(year=1991, month=01, day=12)
    }

    fake_db_api._convert_python_types([expected])
    assert [expected] == result
    assert result[0][u"client"][u"creation"] == 663638400


def test_get_columns_from_description(fake_db_api, project_description):
    assert fake_db_api.get_validation_schema_from_description(project_description) == {

    }