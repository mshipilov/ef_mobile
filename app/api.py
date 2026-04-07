from fastapi import FastAPI, Depends
from fastapi import HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from .models import User
from .schemas import UserToken, UserCreate, UserRead, UserUpdate, UserDelete
from .crud import create_token, create_user, read_user, update_user, delete_user


app = FastAPI()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")
SECRET_KEY = "your_server_private_key"
ALGORITHM = "HS256"


@app.post("/token")
def login(user_data: UserToken):
    token = create_token(user_data) 
    return {"access_token": token, "token_type": "bearer"}



@app.get("/profile")
def get_profile(user_read: UserRead):

    pass

@app.post("/profile")
def create_profile(user_in: UserCreate):
    user = create_user(user_in.model_dump())
    if not user:
        raise HTTPException(status_code=400, detail="Email already registered")
    return {'message': f'You registered new User with id {user.id}'} 

@app.patch("/profile")
def update_profile(user_upd: UserUpdate):
    updated_user = update_user(user_upd.model_dump(exclude_unset=True))  # exclude_unset=True means delete keys with None values
    if not updated_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {"message": f"User with id {updated_user.id} updated successfully"}

@app.delete("/profile")
def delete_profile(user_del: UserDelete):
    user_id = user_del.id
    result = delete_user(user_id)
    if not result:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {"message": f"User with id {user_id} deleted successfully"}

# # frontend needs role_id for each role to create new user
# @app.get("/role")
# def get_roles():
#     pass