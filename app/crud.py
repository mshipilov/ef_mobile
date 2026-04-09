import os
from dotenv import load_dotenv
import platform
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy import select, update, delete
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException
from .models import Base, User, Order, Role, BusinessElement, AccessRolesRule
from .encryption import encrypt_pass, check_encrypred_pass

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

def create_role(user_data: dict):
    new_role = Role(**user_data)
    session.add(new_role)
    try:
        session.commit()
    except IntegrityError as e:
        pg_code = getattr(e.orig, "pgcode")
        if pg_code == UNIQUE_VIOLATION:
            session.rollback()
            raise HTTPException(status_code=400, detail=f"Role with data {user_data} already registered")
        # for other issues re-throw original error
        raise
    session.refresh(new_role)
    return new_role

def read_role(role_id):
    stmt = select(Role).where(Role.id == role_id)
    role = session.execute(stmt).scalars().first()
    return role

def delete_role(role_id):
    role = read_role(role_id)
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    
    try:
        stmt = delete(Role).where(Role.id == role_id)
        session.execute(stmt)
        session.commit()
    except IntegrityError:
        session.rollback()
        raise HTTPException(status_code=400, detail=f"Cannot delete. Foreign key violation.")
    return True

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

# soft delete here
def delete_user(user_id):
    user = read_user(user_id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    stmt = update(User).where(User.id == user_id).values(is_active=False)
    session.execute(stmt)
    session.commit()
    return True


def create_order(user_data: dict):
    new_order = Order(**user_data)
    session.add(new_order)
    session.commit()
    session.refresh(new_order)
    return new_order

def read_order(order_id):
    stmt = select(Order).where(Order.id == order_id)
    order = session.execute(stmt).scalars().first()
    return order

def update_order(user_data: dict):
    order_id = user_data['id']
    order = read_order(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    for field, value in user_data.items():
        setattr(order, field, value)
    session.add(order)
    session.commit()
    session.refresh(order)
    return order

def delete_order(order_id):
    order = read_order(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    stmt = delete(Order).where(Order.id == order_id)
    session.execute(stmt)
    session.commit()
    return True


def create_access_rule(user_data: dict):
    new_access_rule = AccessRolesRule(**user_data)
    session.add(new_access_rule)
    session.commit()
    session.refresh(new_access_rule)
    return new_access_rule

def read_access_rule(access_rule_id):
    stmt = select(AccessRolesRule).where(AccessRolesRule.id == access_rule_id)
    access_rule = session.execute(stmt).scalars().first()
    return access_rule

def update_access_rule(user_data: dict):
    access_rule_id = user_data['id']
    access_rule = read_access_rule(access_rule_id)
    if not access_rule:
        raise HTTPException(status_code=404, detail="Access rule not found")
    for field, value in user_data.items():
        setattr(access_rule, field, value)
    session.add(access_rule)
    session.commit()
    session.refresh(access_rule)
    return access_rule


def delete_access_rule(access_rule_id):
    access_rule = read_access_rule(access_rule_id)
    if not access_rule:
        raise HTTPException(status_code=404, detail="Access rule not found")
    stmt = delete(AccessRolesRule).where(AccessRolesRule.id == access_rule_id)
    session.execute(stmt)
    session.commit()
    return True

def read_all_business_elements():
    stmt = select(BusinessElement)
    business_elements = session.execute(stmt).scalars().all()
    return business_elements

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
            hashed_password=encrypt_pass('1'), 
            role=admin_role
        )
        simple_user1 = User(
            name='Fedor',
            email="user1@example.com", 
            hashed_password=encrypt_pass('1'), 
            role=user_role
        )
        simple_user2 = User(
            name='Vasiliy',
            email="user2@example.com", 
            hashed_password=encrypt_pass('1'),  
            role=user_role
        )
        session.add_all([admin_user, simple_user1, simple_user2])
        session.flush()

        order1 = Order(
            description='order #1',
            user=simple_user1)
        order2 = Order(
            description='order #2',
            user=simple_user2)
        session.add_all([order1, order2])

        # create Business Elements
        user_be = BusinessElement(name="User Management")
        order_be = BusinessElement(name="Order Management")
        role_be = BusinessElement(name="Role Management")
        permission_be = BusinessElement(name="Access Management")

        session.add_all([user_be, order_be, role_be, permission_be])
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
        order_rule = AccessRolesRule(
            role=user_role,
            business_element=order_be,
            read_permission=True,
            create_permission=True,
            update_permission=True,
            delete_permission=True,
        )
        
        session.add_all([user_rule, order_rule])

        # Final Commit
        session.commit()

if __name__ == '__main__':
   initial_db_population()