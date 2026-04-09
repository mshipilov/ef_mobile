from fastapi import FastAPI, Depends, Request
from fastapi import HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from sqlalchemy import select, update
from typing import Annotated
from .models import Base, User, Role
from .schemas import UserCreateBase, UserUpdateBase, UserCreateAdmin, UserUpdateAdmin
from .crud import session, create_user, read_user, update_user, delete_user
from .crud import create_order, read_order, update_order, delete_order
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
def api_create_user(user_in: UserCreateBase):
    user_data = user_in.model_dump()
    # assign user role_id
    stmt = select(Role.id).where(Role.name == "user")
    user_data["role_id"] = session.execute(stmt).scalar_one()

    return create_user(user_data)

# you must be admin to register other roles
@app.post("/admin/user", dependencies=[Depends(RoleChecker("User Management", "create", User))])
def api_create_user_admin(user_in: UserCreateAdmin):
    user_data = user_in.model_dump()
    return create_user(user_data)


@app.get("/profile/{id}", dependencies=[Depends(RoleChecker("User Management", "read", User))])
def api_get_user(id: int,):
    user = read_user(user_id=id)
    return user

# you must authentificate to update your profile
@app.patch("/user")
def api_update_user(
    user_upd: UserUpdateBase,
    current_user = Depends(RoleChecker("User Management", "update", User))):
    user_data = user_upd.model_dump(exclude_unset=True)  # exclude_unset=True means delete keys with None values 
    user_data['id'] = current_user.id  # we update current user
    updated_user = update_user(user_data)     
    return {"message": f"User with id {updated_user.id} updated successfully"}

# you must be admin to update user.role_id for any user
@app.patch("/admin/user/{id}", dependencies=[Depends(RoleChecker("User Management", "update", User))])
def api_update_user_admin(user_upd: UserUpdateAdmin,):
    updated_user = update_user(user_upd.model_dump(exclude_unset=True))
    return {"message": f"User with id {updated_user.id} updated successfully"}

@app.delete("/profile/{id}", dependencies=[Depends(RoleChecker("User Management", "delete", User))])
def api_delete_profile(id: int,):
    delete_user(id)
    return {"message": f"User with id {id} deleted successfully"}

@app.get("/order/{id}")
def api_get_order(id: int):


# # frontend needs role_id for each role to create new user
# @app.get("/role")
# def get_roles():
#     pass

# @app.get("/admin/permissions", dependencies=[Depends(RoleChecker("Permission Management", "read", User))])
# def get_all_permissions():
#     # Fetch all records from AccessRolesRule table
#     return read_all_permissions()

# @app.patch("/admin/permissions/{rule_id}", dependencies=[Depends(RoleChecker("Permission Management", "update", User))])
# def update_permission_rule(rule_id: int, rule_upd: PermissionUpdateSchema):
#     # Update specific flags (read_all, update_all, etc.) for a specific role
#     return update_access_rule(rule_id, rule_upd.model_dump(exclude_unset=True))