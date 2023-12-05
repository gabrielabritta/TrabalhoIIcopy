from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

DB_CONNECTION = 'sqlite:///data\data.db?check_same_thread=False' #string de conexão que passa a conexão com o DB
engine = create_engine(DB_CONNECTION, echo=False)   #cria a engine a partir da string de conexão
Base = declarative_base()                           #cria a Base
Session = sessionmaker(bind=engine)                 #cria a Session
