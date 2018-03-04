# coding utf-8

import pytz
import datetime
from mock import Mock
from pytest import fixture
from dbapi.dbapi import DBApi


@fixture(scope=u"function")
def fake_db_api():
    return DBApi(Mock(), u"project")


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