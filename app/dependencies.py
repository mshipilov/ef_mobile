from typing import Annotated
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi import FastAPI, Depends, Request
from fastapi import HTTPException, status
from .crud import session, create_user, read_user, update_user, delete_user
from .models import Base, User, Role
from .tokenization import encode_token, decode_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

BUSINESS_ELEMENTS_ADMIN_ONLY_ACCESS = ['Role Management', 'Access Management']

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
            model: type[Base],
            ):
        self.element_name = business_element_name  # to which resource we check access (User Management, Order Management, ...)
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
        
        # check business_elements with admin-only access
        if self.element_name in BUSINESS_ELEMENTS_ADMIN_ONLY_ACCESS:
            if current_user.role == 'admin':
                return current_user
            else:
                raise self.access_denied_exception
            
        # check access_roles_rules
        rules = current_user.role.access_roles_rules
        # find the rule for business_element (it always one or None)
        rule = next((r for r in rules if r.business_element.name == self.element_name), None)

        if not rule:  # no rows in access_roles_rule table in DB for given role for given business_element - so user not authorized
            raise self.access_denied_exception
        
        # check broad permission (global access)
        if getattr(rule, f"{self.permission_type}_all_permission", False):  # for example user has read_all_permission - so user authorized
            return current_user
        
        # if user doesn't have global access,
        # check individual permission (personal access)
        if getattr(rule, f"{self.permission_type}_permission", False):
            # CASE: create (resource_id doesn't exist):
            if self.permission_type == "create":
                # allow to create non-user users for admin only
                if self.element_name == 'User Management' and current_user.role == 'admin':
                    return current_user
                # allow to create orders for any user
                if self.element_name == 'Order Management':
                    return current_user
            
            # CASE: read, update, delete (resource_id must exist)
            # check ownership here (e.g., order.owner_id)
            resource_id = request.path_params.get('id')
            if not resource_id:
                raise HTTPException(status_code=400, detail=f"resourse_id not provided in request")
            
            resource = session.get(self.model, resource_id)
            if resource and getattr(resource, "owner_id", None) == current_user.id:
                return current_user

        raise self.access_denied_exception