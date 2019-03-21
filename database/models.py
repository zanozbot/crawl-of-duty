from sqlalchemy import Table
from sqlalchemy.orm import create_session

from database.DatabaseManager import DatabaseManager

databaseManager = DatabaseManager()
Base = databaseManager.get_base()
metadata = databaseManager.get_metadata()
engine = databaseManager.get_engine()

# Reflect each database table we need to use, using metadata
class DataType(Base):
    __table__ = Table('data_type', metadata, autoload=True, schema='crawldb')

class PageType(Base):
    __table__ = Table('page_type', metadata, autoload=True, schema='crawldb')

class Site(Base):
    __table__ = Table('site', metadata, autoload=True, schema='crawldb')

class Page(Base):
    __table__ = Table('page', metadata, autoload=True, schema='crawldb')

class Link(Base):
    __table__ = Table('link', metadata, autoload=True, schema='crawldb')

class PageData(Base):
    __table__ = Table('page_data', metadata, autoload=True, schema='crawldb')

class Image(Base):
    __table__ = Table('image', metadata, autoload=True, schema='crawldb')

# Create a session to use the tables
session = create_session(bind=engine)