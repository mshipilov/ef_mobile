from pydantic import BaseModel, EmailStr, model_validator, Field


class UserCreate(BaseModel):
    name: str
    email: EmailStr  # Validates email format automatically
    pswd: str = Field(exclude=True) 
    repeat_pswd: str = Field(exclude=True) 
    role_id: int

    @model_validator(mode='after')
    def check_passwords_match(self):
        if self.pswd != self.repeat_pswd:
            raise ValueError("Passwords do not match")
        return self