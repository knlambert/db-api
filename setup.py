"""
Setup file describing how to install.
"""
from setuptools import setup

setup(
    name=u'db-api',
    version=u'0.2.1',
    packages=[
        u'dbapi', 
        u'dbapi.adapter'
    ],
    install_requires=[
        u'flask>=1.0.2,<2',
        u"sqlcollection>=0.1.4,<1",
        u"user_api>=0.4.1,<1"
    ]
)