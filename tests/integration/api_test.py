# coding utf-8

import json
import requests
from pytest import fixture
from typing import Dict
from .utils import from_initial_state


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
    from_initial_state()
    # Tenant 1
    ret = session_1.get(
        headers=headers,
        url="http://127.0.0.1:5000/api/db/projects?auto_lookup=1"
    )
    result = json.loads(ret.text)
    assert result["items"][0] == {
        "id": 1,
        "client": {
            "id": 1,
            "name": "Airbus"
        },
        "name": "A350"
    }
    # Tenant 2
    ret = session_2.get(
        headers=headers,
        url="http://127.0.0.1:5000/api/db/projects?auto_lookup=1"
    )
    result = json.loads(ret.text)
    assert result["items"][0] == {
        "id": 1,
        "client": {
            "id": 1,
            "name": "Boeing"
        },
        "name": "747"
    }


def test_insert(
    session_1: requests.Session,
    headers: Dict
):
    from_initial_state()
    # Tenant 1
    ret = session_1.post(
        headers=headers,
        url="http://127.0.0.1:5000/api/db/projects/?auto_lookup=1",
        data=json.dumps({
            "id": 3,
            "name": "A220",
            "client": {
                "id": 1
            }
        })
    )
    result = json.loads(ret.text)
    print(result)
    assert result == {
        "inserted_id": 3
    }
