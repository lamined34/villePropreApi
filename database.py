from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base, Session


#SQLALCHEMY_DATABASE_URL = 'postgresql+psycopg2://postgres:123456789@localhost:5432/Ville_propre'
SQLALCHEMY_DATABASE_URL = 'postgresql://postgres:123456789@localhost:5432/villePropre'

#SQLALCHEMY_DATABASE_URL = 'sqlite:///villePropre.db'

engine = create_engine(
    SQLALCHEMY_DATABASE_URL
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    
    try :
        yield db
    finally :
        db.close()

#By myself testing purpose
def get_db2():
    db = Session(engine)
    return db

