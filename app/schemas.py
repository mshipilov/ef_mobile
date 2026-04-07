from pydantic import BaseModel, EmailStr, model_validator, Field
from typing import Optional


class UserToken(BaseModel):
    user_id: int
    user_name: str
    user_pswd: str


class UserCreate(BaseModel):
    name: str
    email: EmailStr  # Validates email format automatically
    pswd: str
    repeat_pswd: str = Field(exclude=True) 
    role_id: int

    @model_validator(mode='after')
    def check_passwords_match(self):
        if self.pswd != self.repeat_pswd:
            raise ValueError("Passwords do not match")
        return self

class UserRead(BaseModel):
    id: int

class UserUpdate(BaseModel):
    id: int
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    pswd: Optional[str] = None
    repeat_pswd: Optional[str] = Field(None, exclude=True)
    # role_id is not here - I plan to make another api endpoint to change role_id for user

    @model_validator(mode='after')
    def check_passwords_match(self):
        # Only validate if both password fields are actually provided
        if self.pswd is not None or self.repeat_pswd is not None:
            if self.pswd != self.repeat_pswd:
                raise ValueError("Passwords do not match")
        return self
    

class UserDelete(BaseModel):
    id: int
