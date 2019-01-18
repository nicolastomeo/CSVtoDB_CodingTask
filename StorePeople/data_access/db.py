import os

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session
from sqlalchemy.orm import sessionmaker

engine = create_engine(
    os.environ['STOREPEOPLE_DB_CONN'], convert_unicode=True)
#create a scoped session that is thread-local
db_session = scoped_session(sessionmaker(
    autocommit=False, autoflush=False, bind=engine))