# coding utf-8

from user_api.helpers import init_db, add_user, add_customer
db_url = "postgresql://postgres@127.0.0.1"
init_db(db_url=db_url, drop_before=True)
# User tenant 1.
add_customer(db_url, 1)
add_user(
    db_url=db_url,
    jwt_secret="jwt_secret",
    username="admin1",
    email="admin1",
    password="password",
    customer_id=1
)
# User tenant 2.
add_customer(db_url, 2)
add_user(
    db_url=db_url,
    jwt_secret="jwt_secret",
    username="admin2",
    email="admin2",
    password="password",
    customer_id=2
)
