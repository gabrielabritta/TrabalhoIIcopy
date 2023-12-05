from db import Base
from sqlalchemy import Column, Integer, DateTime, Float, Integer, Text

#Implementa a classe DadoCLP a partir da Base do sqlalchemy
class DadoCLP(Base):
    """
    Modelo dos dados do CLP
    """
    #como não temos construtor, usa o da base
    __tablename__ = 'dadoclp' #nome da tabela
    id = Column(Integer, primary_key=True) #id principal
    timestamp = Column(DateTime) #coluna timestamp
    velocity = Column(Float) #coluna temperatura, etc...
    torque = Column(Float)
    pit01 = Column(Float)
    fv01 = Column(Float)
    fit02 = Column(Float)
    fit03 = Column(Float)
    xv1 = Column(Integer)
    xv2 = Column(Integer)
    xv3 = Column(Integer)
    xv4 = Column(Integer)
    xv5 = Column(Integer)
    xv6 = Column(Integer)
    freq = Column(Float)
    current = Column(Float)
    P = Column(Integer)
    Q = Column(Integer)
    S = Column(Integer)
    startType = Column(Text)
    activeMotor = Column(Text)
    inversorFreq = Column(Float)
    
    def get_attr_list(self): #método auxiliar p/ ajudar a printar os dados na tela
        return self.timestamp
