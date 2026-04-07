import jwt
from datetime import datetime, timedelta, timezone
import os
from dotenv import load_dotenv
from fastapi.security import OAuth2PasswordBearer
from fastapi import  Depends, HTTPException, status

load_dotenv()

SECRET_KEY = os.getenv('TOKENIZATION_SECRET_KEY')
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# looks like I don't need to store tokens in DB
# I can put all data (user_id, exp) to payload

def encode_token(user_id: int) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    # The "sub" (subject) claim is standard for the user identifier
    payload = {"sub": str(user_id), "exp": expire}
    encoded_jwt = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def decode_token(token: str) -> dict:
    try:
        # Decode and verify the token
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        return "Token has expired"
    except jwt.InvalidTokenError:
        return "Invalid token"
    
# OAuth2PasswordBearer is used to extract the token from the request header
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Если по входящему запросу не удается определить залогиненного пользователя, выдается ошибка 401. 
# Если пользователь определен, но запрашиваемый ресурс ему не доступен 403 ошибка — Forbidden. 
def get_user_id_from_token(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="User not found",
    )
    token_expired_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token expired",
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            raise credentials_exception
        return int(user_id)
    except jwt.ExpiredSignatureError:
        raise token_expired_exception
    except jwt.InvalidTokenError:
        raise credentials_exception