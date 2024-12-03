from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import sqlite3
import os

# First, let's backup the existing database
def backup_database():
    if os.path.exists('zoho_accounts.db'):
        print("Creating backup of existing database...")
        with open('zoho_accounts.db', 'rb') as source:
            with open('zoho_accounts.db.backup', 'wb') as target:
                target.write(source.read())

# Get existing data
def get_existing_data():
    conn = sqlite3.connect('zoho_accounts.db')
    cursor = conn.cursor()
    cursor.execute('SELECT id, email, app_password, sender_name, is_active, signature FROM zoho_accounts')
    data = cursor.fetchall()
    conn.close()
    return data

# Create new database with updated schema
def create_new_database():
    Base = declarative_base()
    
    class ZohoAccount(Base):
        __tablename__ = 'zoho_accounts'
        
        id = Column(Integer, primary_key=True)
        email = Column(String, unique=True, nullable=False)
        app_password = Column(String, nullable=False)
        sender_name = Column(String, nullable=False)
        is_active = Column(Integer, default=1)
        signature = Column(String, nullable=False, default='Regards\n{sender_name}\nPartnership Manager\nBlackBurn Media')
        last_email_sent = Column(DateTime, nullable=True)
    
    engine = create_engine('sqlite:///zoho_accounts.db')
    Base.metadata.create_all(engine)
    return engine, ZohoAccount

def migrate_data():
    print("Starting database migration...")
    
    # Backup existing database
    backup_database()
    
    # Get existing data
    existing_data = get_existing_data()
    
    # Remove old database
    if os.path.exists('zoho_accounts.db'):
        os.remove('zoho_accounts.db')
    
    # Create new database with updated schema
    engine, ZohoAccount = create_new_database()
    Session = sessionmaker(bind=engine)
    session = Session()
    
    # Insert existing data into new database
    for record in existing_data:
        account = ZohoAccount(
            id=record[0],
            email=record[1],
            app_password=record[2],
            sender_name=record[3],
            is_active=record[4],
            signature=record[5],
            last_email_sent=None
        )
        session.add(account)
    
    session.commit()
    print("Migration completed successfully!")
    print(f"Migrated {len(existing_data)} accounts")
    print("A backup of your old database has been saved as 'zoho_accounts.db.backup'")

if __name__ == "__main__":
    migrate_data() 