# coding utf-8
from sqlalchemy import (
    Column,
    String,
    Integer,
    ForeignKey
)
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class Project(Base):

    __tablename__ = "project"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255))
    client = Column('client', Integer, ForeignKey('client.id'))


class Client(Base):

    __tablename__ = "client"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255))
