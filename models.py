from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

Base = declarative_base()
engine = create_engine('sqlite:///zoho_accounts.db')
Session = sessionmaker(bind=engine)

class ZohoAccount(Base):
    __tablename__ = 'zoho_accounts'
    
    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True, nullable=False)
    app_password = Column(String, nullable=False)
    sender_name = Column(String, nullable=False)
    is_active = Column(Integer, default=1)
    signature = Column(String, nullable=False, default='Regards\n{sender_name}\nPartnership Manager\nBlackBurn Media')
    last_email_sent = Column(DateTime, nullable=True)

Base.metadata.create_all(engine) 