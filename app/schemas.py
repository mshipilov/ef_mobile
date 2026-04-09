from pydantic import BaseModel, EmailStr, model_validator, Field
from typing import Optional


class UserCreateBase(BaseModel):
    name: str
    email: EmailStr  # Validates email format automatically
    pswd: str
    repeat_pswd: str = Field(exclude=True) 
    # Optional: Forbid extra fields so they can't sneak in a 'role_id'
    #model_config = ConfigDict(extra="forbid")

    @model_validator(mode='after')
    def check_passwords_match(self):
        if self.pswd != self.repeat_pswd:
            raise ValueError("Passwords do not match")
        return self
    
class UserUpdateBase(UserCreateBase):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    pswd: Optional[str] = None
    repeat_pswd: Optional[str] = Field(None, exclude=True)

class UserCreateAdmin(UserCreateBase):
    role_id: int

class UserUpdateAdmin(UserUpdateBase):
    role_id: Optional[int] = None  # Admins can explicitly set the role
    

class OrderCreate(BaseModel):
    description: str

class RoleCreate(BaseModel):
    name: str

class AccessRuleCreate(BaseModel):
    role_id: int
    business_element_id: int
    read_permission: Optional[bool] = None
    read_all_permission: Optional[bool] = None
    create_permission: Optional[bool] = None
    update_permission: Optional[bool] = None
    update_all_permission: Optional[bool] = None
    delete_permission: Optional[bool] = None
    delete_all_permission: Optional[bool] = None