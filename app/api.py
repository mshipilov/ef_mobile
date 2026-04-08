from fastapi import FastAPI, Depends, Request
from fastapi import HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from sqlalchemy import select, update
from typing import Annotated
from .models import Base, User, Role
from .schemas import UserCreateBase, UserUpdateBase, UserCreateAdmin, UserUpdateAdmin
from .crud import session, create_user, read_user, update_user, delete_user
from .tokenization import encode_token, decode_token
from .encryption import check_encrypred_pass

app = FastAPI()


SECRET_KEY = "your_server_private_key"
ALGORITHM = "HS256"

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

SECRET_KEY = "your_server_private_key"
ALGORITHM = "HS256"

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Если по входящему запросу не удается определить залогиненного пользователя, выдается ошибка 401. 
# Если пользователь определен, но запрашиваемый ресурс ему не доступен 403 ошибка — Forbidden. 
def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    payload = decode_token(token)
    print(payload)
    user_id = payload['sub']
    user = read_user(user_id=user_id)
    return user

def get_current_active_user(current_user: Annotated[User, Depends(get_current_user)],):
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

class RoleChecker:
    
    def __init__(
            self, 
            business_element_name: str, 
            permission_type: str, 
            model: type[Base] = None,
            ):
        self.element_name = business_element_name
        self.permission_type = permission_type # read, update, delete
        self.model = model
        self.access_denied_exception =HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied: Missing {self.permission_type} for {self.element_name}"
        )

    def __call__(
            self, 
            request: Request,
            current_user: Annotated[User, Depends(get_current_active_user)],
            ):
        # process "Public" requests with no check for access_roles_rules
        if self.element_name == "Public":
            return None
        
        rules = current_user.role.access_roles_rules
        # find the rule for  business element (it always one or None)
        rule = next((r for r in rules if r.business_element.name == self.element_name), None)

        if not rule:
            raise self.access_denied_exception
        
        # check broad permission (global access)
        if getattr(rule, f"{self.permission_type}_all_permission", False):  # for example, read_all_permission
            return current_user
        
        # check individual permission (personal access)
        if getattr(rule, f"{self.permission_type}_permission", False):
            # create (resource_id doesn't exist):
            if request.method == "POST":
                return current_user
            # read, update, delete (resource_id must exist):
            resource_id = request.path_params.get('id')
            if not resource_id:
                raise HTTPException(status_code=400, detail=f"resourse_id not provided in request")

            # user creates profile via self.element_name == "Public". Here only admins 
            if self.element_name in ["User Management", "Permission Management"]:
                raise HTTPException(status_code=403, detail=f"Access denied: only admin has access")
            
            # Case: Generic Ownership (e.g., Orders)
            elif self.model:
                resource = session.get(self.model, resource_id)
                if resource and getattr(resource, "owner_id", None) == current_user.id:
                    return current_user

        raise HTTPException(status_code=403, detail=f"Access denied: Missing {self.permission_type} for {self.element_name}")
        


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


@app.get("/profile/{id}", dependencies=[Depends(RoleChecker("User Management", "read", User))])
def get_profile(id: int,):
    user = read_user(user_id=id)
    return user

@app.post("/register", dependencies=[Depends(RoleChecker("Public", "create", User))])
def public_register(user_in: UserCreateBase):
    user_data = user_in.model_dump()
    # Manually assign user role ID
    stmt = select(Role.id).where(Role.name == "user")
    user_data["role_id"] = session.execute(stmt).scalar_one()

    return create_user(user_data)

@app.post("/admin/create-user", dependencies=[Depends(RoleChecker("User Management", "create", User))])
def admin_create_user(user_in: UserCreateAdmin):
    return create_user(user_in.model_dump())

@app.patch("/profile", dependencies=[Depends(RoleChecker("User Management", "update", User))])
def update_profile(user_upd: UserUpdateBase,):
    updated_user = update_user(user_upd.model_dump(exclude_unset=True))  # exclude_unset=True means delete keys with None values    
    return {"message": f"User with id {updated_user.id} updated successfully"}

@app.delete("/profile/{id}", dependencies=[Depends(RoleChecker("User Management", "delete", User))])
def delete_profile(id: int,):
    delete_user(id)
    return {"message": f"User with id {id} deleted successfully"}

# # frontend needs role_id for each role to create new user
# @app.get("/role")
# def get_roles():
#     pass

@app.get("/admin/permissions", dependencies=[Depends(RoleChecker("Permission Management", "read", User))])
def get_all_permissions():
    # Fetch all records from AccessRolesRule table
    return read_all_permissions()

@app.patch("/admin/permissions/{rule_id}", dependencies=[Depends(RoleChecker("Permission Management", "update", User))])
def update_permission_rule(rule_id: int, rule_upd: PermissionUpdateSchema):
    # Update specific flags (read_all, update_all, etc.) for a specific role
    return update_access_rule(rule_id, rule_upd.model_dump(exclude_unset=True))