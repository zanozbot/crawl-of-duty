from sqlalchemy import *
from sqlalchemy.ext.declarative import declarative_base

class DatabaseManager:
    def __init__(self):
        # Create and engine and get the metadata
        self.Base = declarative_base()
        self.engine = create_engine("postgresql://docker:docker@192.168.99.100:5432/postgres")
        self.metadata = MetaData(bind=self.engine)

    def get_base(self):
        return self.Base

    def get_metadata(self):
        return self.metadata

    def get_engine(self):
        return self.engine
