# coding utf-8

from pytest import fixture
from sqlalchemy import create_engine, MetaData
from .models import Base, Project, Client
from sqlalchemy.orm import sessionmaker

@fixture(scope="function")
def from_initial_state():
    """
    This fixture destroys and create again the postgres database
    to always execute each integration test from the same state.
    """
    clients = [
        ["Airbus"],
        ["Boeing"]
    ]
    projects = [
        [("A350", 1), ("A320", 1)],
        [("747", 1), ("737", 1)]
    ]
    for index in [1, 2]:
        db_url = "postgresql://postgres:postgresql@127.0.0.1/" \
            "app_tenant_{}".format(index)

        engine = create_engine(db_url, echo=False)

        meta = MetaData()
        meta.reflect(bind=engine, views=True)

        for tbl in reversed(meta.sorted_tables):
            engine.execute(tbl.delete())

        Base.metadata.create_all(bind=engine)
        
        # Filling DB
        session = sessionmaker(engine)()
        for _id, name in enumerate(clients[index-1]):
            client = Client(
                id=_id+1,
                name=name
            )
            session.add(client)
            session.commit()

        for _id, (name, client_id) in enumerate(projects[index-1]):
            project = Project(
                id=_id+1,
                name=name,
                client=client_id
            )
            session.add(project)
            session.commit()

        session.close()
        
        