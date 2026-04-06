from fastapi import HTTPException, status, Depends
from sqlalchemy.orm import Session
from sqlalchemy import select
from .models import User, Role, Permission

def check_permissions(user: User, resource: str, action: str, db: Session):

    if not user.is_active:
        raise HTTPException(status_code=403, detail="User is inactive")

    has_permission = any(
        permission.resource_name == resource and permission.action == action 
        for permission in user.role.permissions
    )

    if not has_permission:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Not enough permissions for {User} to {resource}:{action}"
        )
    
    return True


class PermissionChecker:
    def __init__(self, resource: str, action: str):
        self.resource = resource
        self.action = action

    def __call__(self, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
        # get_current_user — это твоя функция аутентификации (извлечение юзера из токена)
        if check_permissions(user, self.resource, self.action, db):
            return user