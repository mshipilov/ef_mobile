from fastapi import FastAPI, Depends, Request
from fastapi import HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from sqlalchemy import select, update
from typing import Annotated
from .models import Base, User, Order, Role, AccessRolesRule
from .schemas import UserCreateBase, UserUpdateBase, UserCreateAdmin, UserUpdateAdmin
from .schemas import OrderCreate, RoleCreate, AccessRuleCreate
from .crud import session, create_user, read_user, update_user, delete_user
from .crud import create_order, read_order, update_order, delete_order
from .crud import create_role, read_role, delete_role
from .crud import create_access_rule, read_access_rule, update_access_rule, delete_access_rule
from .crud import read_all_business_elements

from .tokenization import encode_token, decode_token
from .encryption import check_encrypred_pass
from .dependencies import RoleChecker

app = FastAPI()

@app.post("/token")
def login(form_data: Annotated[OAuth2PasswordRequestForm, Depends()]):
    email = form_data.username
    password = form_data.password
    user = read_user(email=email)
    if not user:
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    if not check_encrypred_pass(password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    token = encode_token(user.id) 

    return {"access_token": token, "token_type": "bearer"}


# no authentification required to register a user
@app.post("/user")  
def user_create(user_in: UserCreateBase):
    user_data = user_in.model_dump()
    # assign user role_id
    stmt = select(Role.id).where(Role.name == "user")
    user_data["role_id"] = session.execute(stmt).scalar_one()

    return create_user(user_data)

# you must be admin to register other roles
@app.post("/admin/user", dependencies=[Depends(RoleChecker("User Management", "create", User))])
def user_create_admin(user_in: UserCreateAdmin):
    user_data = user_in.model_dump()
    return create_user(user_data)

@app.get("/profile/{id}", dependencies=[Depends(RoleChecker("User Management", "read", User))])
def user_read(id: int,):
    user = read_user(user_id=id)
    return user

# you must authentificate to update your profile
# {id} here in route only for RoleChecker. We can receive id from current_user.id
@app.patch("/user/{id}")
def user_update(
    user_in: UserUpdateBase,
    current_user = Depends(RoleChecker("User Management", "update", User))):
    user_data = user_in.model_dump(exclude_unset=True)  # exclude_unset=True means delete keys with None values 
    user_data['id'] = current_user.id  # we update current user
    updated_user = update_user(user_data)     
    return {"message": f"User with id {updated_user.id} updated successfully"}

# you must be admin to update user.role_id for any user
@app.patch("/admin/user/{id}", dependencies=[Depends(RoleChecker("User Management", "update", User))])
def admin_user_update(user_in: UserUpdateAdmin,):
    updated_user = update_user(user_in.model_dump(exclude_unset=True))
    return {"message": f"User with id {updated_user.id} updated successfully"}

@app.delete("/profile/{id}", dependencies=[Depends(RoleChecker("User Management", "delete", User))])
def user_delete(id: int,):
    delete_user(id)
    return {"message": f"User with id {id} deleted successfully"}


@app.post("/order", dependencies=[Depends(RoleChecker("Order Management", "create", Order))])
def order_create(
    user_in: OrderCreate,
    current_user=Depends(RoleChecker("Order Management", "create", Order)),
    ):
    user_id = current_user.id
    user_data = user_in.model_dump()
    user_data['owner_id'] = user_id
    return create_order(user_data)

@app.get("/order/{id}", dependencies=[Depends(RoleChecker("Order Management", "read", Order))])
def order_read(id: int):
    return read_order(id)

@app.patch("/order/{id}", dependencies=[Depends(RoleChecker("Order Management", "update", Order))])
def order_update(
    id: int,
    user_in: OrderCreate,
    ):
    user_data = user_in.model_dump(exclude_unset=True)
    user_data['id'] = id
    updated_order = update_order(user_data)
    return {"message": f"Order with id {updated_order.id} updated successfully"}

@app.delete("/order/{id}", dependencies=[Depends(RoleChecker("Order Management", "delete", Order))])
def order_delete(id: int,):
    delete_order(id)
    return {"message": f"Order with id {id} deleted successfully"}


@app.post("/admin/role", dependencies=[Depends(RoleChecker("Role Management", "create"))])
def role_create(
    user_in: RoleCreate,
    ):
    return create_role(user_in.model_dump())

@app.get("/admin/role/{id}", dependencies=[Depends(RoleChecker("Role Management", "read"))])
def role_read(id: int):
    return read_role(id)

@app.delete("/admin/role/{id}", dependencies=[Depends(RoleChecker("Role Management", "delete"))])
def role_delete(id: int,):
    delete_role(id)
    return {"message": f"Role with id {id} deleted successfully"}


@app.post("/admin/access_rule", dependencies=[Depends(RoleChecker("Access Management", "create"))])
def access_rule_create(
    user_in: AccessRuleCreate,
    ):
    return create_access_rule(user_in.model_dump())

@app.get("/admin/access_rule/{id}", dependencies=[Depends(RoleChecker("Access Management", "read"))])
def access_rule_read(id: int):
    return read_access_rule(id)

@app.patch("/admin/access_rule/{id}", dependencies=[Depends(RoleChecker("Access Management", "update"))])
def access_rule_update(
    id: int,
    user_in: OrderCreate,
    ):
    user_data = user_in.model_dump(exclude_unset=True)
    user_data['id'] = id
    updated_access_rule = update_access_rule(user_data)
    return {"message": f"Access rule with id {updated_access_rule.id} updated successfully"}

@app.delete("/admin/access_rule/{id}", dependencies=[Depends(RoleChecker("Access Management", "delete"))])
def access_rule_delete(id: int,):
    delete_access_rule(id)
    return {"message": f"Access rule with id {id} deleted successfully"}

@app.get("/admin/business_elements", dependencies=[Depends(RoleChecker("Business Element Management", "read"))])
def business_elements_read():
    return read_all_business_elements()