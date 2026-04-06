from fastapi import FastAPI, Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from .permission_service import PermissionChecker
from .models import User
from .schemas import UserCreate
from .tokenization import create_token
from .crud import create_user


app = FastAPI()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")
SECRET_KEY = "your_server_private_key"
ALGORITHM = "HS256"


@app.post("/token")
def login_for_access_token(form_data):
    token = create_token(user_id)



@app.get("/profile")
def get_profile(
    session: Session = Depends(get_session),
    current_user: User = Depends(PermissionChecker(resource="orders", action="read"))
):
    pass

@app.post("/profile")
def create_profile(user_in: UserCreate):
    user = create_user(user_in)
    return {'message': f'You registered new User with id {user.id}'}

@app.patch("/profile")
def update_profile(
    current_user: User = Depends(PermissionChecker(resource="orders", action="create"))
):
    return {"message": "Заказ успешно создан"}

@app.delete("/profile")
def delete_profile(
    current_user: User = Depends(PermissionChecker(resource="orders", action="delete"))
):
    return {"message": "Заказ удален"}

# frontend needs role_id for each role to create new user
@app.get("/role")
def get_roles():
    pass