# coding utf-8

import json
import requests
from pytest import fixture
from typing import Dict


@fixture(scope="function")
def session_1(headers: Dict) -> requests.Session:
    session = requests.Session()
    session.post(
        "http://127.0.0.1:5000/api/users/login",
        data=json.dumps({
            "email": "admin1",
            "password": "password"
        }),
        headers=headers
    )
    return session


@fixture(scope="function")
def session_2(headers: Dict) -> requests.Session:
    session = requests.Session()
    session.post(
        "http://127.0.0.1:5000/api/users/login",
        data=json.dumps({
            "email": "admin2",
            "password": "password"
        }),
        headers=headers
    )
    return session


@fixture(scope="function")
def headers() -> Dict:
    return {
        "Content-Type": "application/json"
    }


def test_list_isolated_tenants(
    session_1: requests.Session,
    session_2: requests.Session,
    headers: Dict
):
    # Tenant 1
    ret = session_1.get(
        headers=headers,
        url="http://127.0.0.1:5000/api/db/projects"
    )
    result = json.loads(ret.text)
    assert result["items"][0] == {
        "id": 1,
        "client": 1,
        "name": "A350"
    }
    # Tenant 2
    ret = session_2.get(
        headers=headers,
        url="http://127.0.0.1:5000/api/db/projects"
    )
    result = json.loads(ret.text)
    assert result["items"][0] == {
        "id": 1,
        "client": 1,
        "name": "747"
    }

    