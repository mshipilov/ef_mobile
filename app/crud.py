import os
from dotenv import load_dotenv
import platform
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException
from .models import Base, User, Role, BusinessElement, AccessRolesRule
from .encryption import encrypt_pass, check_encrypred_pass
from .tokenization import encode_token

load_dotenv() 

DB_USER = os.getenv('POSTGRES_USER')
DB_PASS = os.getenv('POSTGRES_PASSWORD')
DB_NAME = os.getenv('POSTGRES_DB_NAME')
# on Windows use forwarded port from localhost to Docker container localhost:5432->pgdatabase:5432
# on Linux (this means we inside Docker container) use container name pgdatabase:5432
DB_HOST='localhost' if platform.system() == 'Windows' else 'pgdatabase'
DB_PORT=5432

UNIQUE_VIOLATION = "23505"  # pg error code


database_url = f'postgresql+psycopg2://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}'
engine = create_engine(database_url, echo=True)
session = Session(engine)

# create tables if not exist
Base.metadata.create_all(engine)

# def create_token(user_data):
#     user_id = user_data['user_id']
#     user = read_user(user_id=user_id)
#     if not user:
#         return None
#     if not check_encrypred_pass(user_data['user_pswd'], user.hashed_password):
#         return False
#     token = encode_token(user_id)
    
#     return token




def create_role(name):
    return Role(name=name)


def read_role(name):
    stmt = select(Role).where(Role.name == name)
    role = session.execute(stmt).scalars().first()
    return role


def create_user(user_data: dict):
    hashed_pass = encrypt_pass(user_data.pop('pswd'))
    new_user = User(**user_data, hashed_password=hashed_pass) 
    session.add(new_user)
    try:
        session.commit()
    except IntegrityError as e:
        pg_code = getattr(e.orig, "pgcode")
        # user already exists
        if pg_code == UNIQUE_VIOLATION:
            session.rollback()
            raise HTTPException(status_code=400, detail="Email already registered")
        # for other issues re-throw original error
        raise
    session.refresh(new_user)
    return new_user


def read_user(*, user_id=None, email=None):
    stmt = select(User)
    
    if user_id:
        stmt = stmt.where(User.id == user_id)
    elif email:
        stmt = stmt.where(User.email == email)
    else:
        return None

    return session.execute(stmt).scalars().first()
    


def update_user(user_data: dict):
    user_id = user_data['id']
    user = read_user(user_id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if "pswd" in user_data:
        password = user_data.pop("pswd")
        user.hashed_password = encrypt_pass(password)
    
    for field, value in user_data.items():
        setattr(user, field, value)
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


def delete_user(user_id):
    user = read_user(user_id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    stmt = update(User).where(User.id == user_id).values(is_active=False)
    session.execute(stmt)
    session.commit()
    return True


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
        permission_be = BusinessElement(name="Permissions Management")
        session.add([user_be, permission_be])
        session.flush()

        # create Access Rules (Write Access for Admin on User Management)
        user_rule = AccessRolesRule(
            role=user_role,
            business_element=user_be,
            read_permission=True,
            create_permission=True,
            update_permission=True,
            delete_permission=True,
        )
        admin_rule = AccessRolesRule(
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
        
        session.add_all([user_rule, admin_rule])

        # Final Commit
        session.commit()

if __name__ == '__main__':
   initial_db_population()