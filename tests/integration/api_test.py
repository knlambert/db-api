# coding utf-8

import json
import requests
import base64
from pytest import fixture
from typing import Dict


@fixture(scope="function")
def session(headers: Dict) -> requests.Session:
    session = requests.Session()
    session.post(
        "http://127.0.0.1:5000/api/users/login",
        data=json.dumps({
            "email": "admin",
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

def test_list(session: requests.Session, headers: Dict):
    result = session.get(
        headers=headers,
        url="http://127.0.0.1:5000/api/users"
    )
    print(result)
    pass