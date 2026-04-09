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
    