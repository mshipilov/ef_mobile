import os
from dotenv import load_dotenv
import platform
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy import select, update
from .schemas import UserCreate
from .models import Base, User, Role, BusinessElement, AccessRolesRule
from .encryption import encrypt_pass, check_encrypred_pass

load_dotenv() 

DB_USER = os.getenv('POSTGRES_USER')
DB_PASS = os.getenv('POSTGRES_PASSWORD')
DB_NAME = os.getenv('POSTGRES_DB_NAME')
# on Windows use forwarded port from localhost to Docker container localhost:5432->pgdatabase:5432
# on Linux (this means we inside Docker container) use container name pgdatabase:5432
DB_HOST='localhost' if platform.system() == 'Windows' else 'pgdatabase'
DB_PORT=5432


database_url = f'postgresql+psycopg2://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}'
engine = create_engine(database_url, echo=True)
session = Session(engine)

# create tables if not exist
Base.metadata.create_all(engine)

def authenticate_user(fake_db, username: str, password: str):
    user = get_user(fake_db, username)
    if not user:
        verify_password(password, DUMMY_HASH)
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user


def get_role(name):
    stmt = select(Role).where(Role.name == name)
    role = session.execute(stmt).scalars().first()
    return role

def create_role(name):
    return Role(name=name)


def get_user(email):
    stmt = select(User).where(User.email == email)
    user = session.execute(stmt).scalars().first()
    return user


def create_user(user_in: UserCreate):
    user_data = user_in.model_dump()
    hashed_pass = encrypt_pass(user_data['pass'])
    new_user = User(**user_data, hashed_password=hashed_pass) 
    return new_user


def initial_db_population():
    with Session(engine) as session:
        # create roles
        admin_role = Role(name="admin")
        user_role = Role(name="user")
        session.add_all([admin_role, user_role])
        session.flush() # Flush to get IDs back without committing yet
        # create users
        admin_user = User(
            name='Ivan',
            email="admin@example.com", 
            hashed_password="secure_admin_hash", 
            role=admin_role
        )
        simple_user = User(
            name='Fedor',
            email="user@example.com", 
            hashed_password="secure_user_hash", 
            role=user_role
        )
        session.add_all([admin_user, simple_user])

        # create Business Elements
        user_be = BusinessElement(name="User Management")
        session.add(user_be)
        session.flush()

        # create Access Rules (Write Access for Admin on User Management)
        user_write_rule = AccessRolesRule(
            role=user_role,
            business_element=user_be,
            read_permission=True,
            create_permission=True,
            update_permission=True,
            delete_permission=True,
        )
        admin_write_rule = AccessRolesRule(
            role=admin_role,
            business_element=user_be,
            read_permission=True,
            create_permission=True,
            update_permission=True,
            delete_permission=True,
            read_all_permission=True,
            update_all_permission=True,
            delete_all_permission=True,
        )
        session.add_all([user_write_rule, admin_write_rule])

        # Final Commit
        session.commit()

if __name__ == '__main__':
   initial_db_population()