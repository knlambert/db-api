# coding utf-8

import datetime
from mock import Mock
from pytest import fixture
from dbapi.dbapi import DBApi


@fixture(scope=u"function")
def stubbed_db_api():
    return DBApi(Mock(), u"project")


@fixture(scope=u"function")
def hour_description():
    return {u'fields': [
        {u'autoincrement': True, u'nullable': False, u'type': u'integer', u'name': u'id', u'primary_key': True},
        {u'nullable': True, u'type': u'string', u'name': u'issue', u'primary_key': False},
        {u'nullable': False, u'type': u'datetime', u'name': u'started_at', u'primary_key': False},
        {u'autoincrement': False, u'nullable': False, u'type': u'integer', u'name': u'minutes', u'primary_key': False},
        {u'nullable': True, u'type': u'string', u'name': u'comments', u'primary_key': False},
        {u'name': u'project', u'nullable': False, u'autoincrement': False, u'nested_description': {u'fields': [
            {u'autoincrement': True, u'nullable': False, u'type': u'integer', u'name': u'id', u'primary_key': True},
            {u'nullable': False, u'type': u'string', u'name': u'name', u'primary_key': False},
            {u'autoincrement': False, u'nullable': False, u'type': u'integer', u'name': u'client',
             u'primary_key': False},
            {u'autoincrement': False, u'nullable': True, u'type': u'integer', u'name': u'provisioned_hours',
             u'primary_key': False},
            {u'nullable': False, u'type': u'datetime', u'name': u'started_at', u'primary_key': False},
            {u'nullable': True, u'type': u'string', u'name': u'code', u'primary_key': False}], u"foreignField": u"id",
            u'as': u'project',
            u'table': u'project'},
         u'type': u'integer', u'primary_key': False},
        {u'name': u'affected_to', u'nullable': False, u'autoincrement': False, u'nested_description': {u'fields': [
            {u'autoincrement': True, u'nullable': False, u'type': u'integer', u'name': u'id', u'primary_key': True},
            {u'nullable': False, u'type': u'string', u'name': u'email', u'primary_key': False},
            {u'nullable': False, u'type': u'string', u'name': u'name', u'primary_key': False},
            {u'autoincrement': False, u'nullable': False, u'type': u'integer', u'name': u'min_hours_per_week',
             u'primary_key': False},
            {u'autoincrement': False, u'nullable': False, u'type': u'integer', u'name': u'default_role',
             u'primary_key': False}], u'as': u'affected_to', u"foreignField": u"id", u'table': u'_user'},
         u'type': u'integer',
         u'primary_key': False}], u'as': u'hour', u'table': u'hour'}


@fixture(scope=u"function")
def project_description():
    return {u'fields': [
        {u'autoincrement': True, u'nullable': False, u'type': u'integer', u'name': u'id', u'primary_key': True},
        {u'name': u'client', u'nullable': False, u'autoincrement': False, u'nested_description': {u'fields': [
            {u'autoincrement': True, u'nullable': False, u'type': u'integer', u'name': u'id', u'primary_key': True},
            {u'nullable': False, u'type': u'string', u'name': u'name', u'primary_key': False}], u'as': u'client',
            u"foreignField": u"id", u'table': u'client'},
         u'type': u'integer', u'primary_key': False},
        {u'autoincrement': False, u'nullable': True, u'type': u'float', u'name': u'provisioned_hours',
         u'primary_key': False},
        {u'nullable': False, u'type': u'datetime', u'name': u'started_at', u'primary_key': False},
        {u'nullable': True, u'type': u'string', u'name': u'code', u'primary_key': False}], u'as': u'project',
        u'table': u'project'}


def test__get_columns_name_types_from_description(stubbed_db_api, project_description):
    result = stubbed_db_api._get_columns_name_types_from_description(project_description)
    assert result == [
        (u"id", u"integer"),
        (u"client.id", u"integer"),
        (u"client.name", u"string"),
        (u"provisioned_hours", u"float"),
        (u"started_at", u"datetime"),
        (u"code", u"string")
    ]


def test_get_validation_schema(stubbed_db_api, project_description):
    validation_schema = stubbed_db_api.get_validation_schema(project_description)

    for key in [u"id", u"client", u"provisioned_hours", u"started_at"]:
        assert key in validation_schema

    assert validation_schema[u"id"] == {
        u"required": False,
        u"type": u"integer",
        u"nullable": False
    }

    assert validation_schema[u"provisioned_hours"] == {
        u"required": False,
        u"type": u"float",
        u"nullable": True
    }

    assert validation_schema[u"started_at"][u"type"] == u"datetime"
    assert validation_schema[u"started_at"][u"required"]
    assert not validation_schema[u"started_at"][u"nullable"]
    assert callable(validation_schema[u"started_at"][u"coerce"])

    assert validation_schema[u"client"] == {
        u"type": u"dict",
        u"required": True,
        u"nullable": False,
        u"purge_unknown": True,
        u"schema": {
            u"id": {
                u"required": True,
                u"type": u"integer",
                u"nullable": False
            }
        }
    }


def test_get_validation_schema_update(stubbed_db_api, project_description):
    validation_schema = stubbed_db_api.get_validation_schema(project_description, is_update=True)

    for key in [u"id", u"client", u"provisioned_hours", u"started_at"]:
        assert key in validation_schema

    assert validation_schema[u"id"] == {
        u"required": False,
        u"type": u"integer",
        u"nullable": False
    }

    assert validation_schema[u"provisioned_hours"] == {
        u"required": False,
        u"type": u"float",
        u"nullable": True
    }

    assert validation_schema[u"started_at"][u"type"] == u"datetime"
    assert not validation_schema[u"started_at"][u"required"]
    assert not validation_schema[u"started_at"][u"nullable"]
    assert callable(validation_schema[u"started_at"][u"coerce"])

    assert validation_schema[u"client"] == {
        u"type": u"dict",
        u"required": False,
        u"nullable": False,
        u"schema": {
            u"id": {
                u"required": False,
                u"type": u"integer",
                u"nullable": False
            },
            u"name": {
                u"required": False,
                u"type": u"string",
                u"nullable": False
            }

        }
    }


def test_get_validation_schema_update_no_deep(stubbed_db_api, project_description):
    validation_schema = stubbed_db_api.get_validation_schema(
        project_description,
        is_update=True,
        deep_update=False
    )

    for key in [u"id", u"client", u"provisioned_hours", u"started_at"]:
        assert key in validation_schema

    assert validation_schema[u"id"] == {
        u"required": False,
        u"type": u"integer",
        u"nullable": False
    }

    assert validation_schema[u"provisioned_hours"] == {
        u"required": False,
        u"type": u"float",
        u"nullable": True
    }

    assert validation_schema[u"started_at"][u"type"] == u"datetime"
    assert not validation_schema[u"started_at"][u"required"]
    assert not validation_schema[u"started_at"][u"nullable"]
    assert callable(validation_schema[u"started_at"][u"coerce"])

    assert validation_schema[u"client"] == {
        u"type": u"dict",
        u"required": False,
        u"nullable": False,
        u"purge_unknown": True,
        u"schema": {
            u"id": {
                u"required": False,
                u"type": u"integer",
                u"nullable": False
            }
        }
    }


def test__convert_python_types(stubbed_db_api):
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
    result = stubbed_db_api._convert_python_types([expected])
    assert [expected] == result
    assert result[0][u"started_at"] == 1520198852
    assert isinstance(result[0][u"started_at"], int)
    # With recursion, date
    expected[u"client"] = {
        u"id": 2,
        u"name": u"Awesome client.",
        u"creation": datetime.date(year=1991, month=1, day=12)
    }

    stubbed_db_api._convert_python_types([expected])
    assert [expected] == result
    assert result[0][u"client"][u"creation"] == 663638400


def test_coerce_method_datetime(stubbed_db_api):
    assert stubbed_db_api._get_timestamp_coerce(u"datetime")(685792800) == datetime.datetime(
        year=1991,
        month=9,
        day=25,
        hour=10,
        minute=00
    )


def test_coerce_method_date(stubbed_db_api):
    # 25/09/1991 23:59:59
    assert stubbed_db_api._get_timestamp_coerce(u"date")(685843199) == datetime.date(
        year=1991,
        month=9,
        day=25
    )
