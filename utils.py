from datetime import datetime, timedelta, timezone
from typing import Annotated
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from sqlalchemy import and_
import jwt
from jwt.exceptions import InvalidKeyTypeError #InvalidTokenError
from passlib.context import CryptContext
import os
from schemas import TokenData, UtilisateurOut
from database import get_db
from models import Utilisateur
import http.client
import json
import random


SECRET_KEY = os.getenv("SECRET_KEY","default-secret-key")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

NimbaACCOUNT_SID = os.getenv("NimbaACCOUNT_SID")
NimbaAUTH_TOKEN = os.getenv("NimbaAUTH_TOKEN")
NIMBA_SECRET_TOKEN = os.getenv("NIMBA_SECRET_TOKEN")
NimbaPHONE_NUMBER = os.getenv("NimbaPHONE_NUMBER")

conn = http.client.HTTPSConnection("api.nimbasms.com")


# Configure passlib pour utiliser bcrypt pour le hachage des mots de passe
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

#Copier depuis le main
UPLOAD_DIRECTORY_COPIE_PI = "static/uploads/copie_pi"
UPLOAD_DIRECTORY_LOGO_PME = "static/uploads/logo_pme"

def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)



def create_access_token(data: dict):
    to_encode = data.copy()

    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, str(SECRET_KEY), algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)], db : Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int = payload.get("user_id")
        role: str = payload.get("role")
        if user_id is None or role is None:
            raise credentials_exception
        token_data = TokenData(user_id=str(user_id), role=role)
    except InvalidKeyTypeError: #InvalidTokenError qui était écrit
        raise credentials_exception
    user = db.query(Utilisateur).filter(and_(Utilisateur.id==token_data.user_id, Utilisateur.is_actif==True)).first()
    if user is None:
        raise credentials_exception
    return user


def role_required(roles: list[str]):
    def role_verification(current_user: UtilisateurOut = Depends(get_current_user)):
        if current_user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Vous n'avez pas l'autorisation d'accéder à cette ressource."
            )
        return current_user
    return role_verification


def envoie_sms(num_phone: str, message:str):
    conn = http.client.HTTPSConnection("api.nimbasms.com")


    headers = {
    "authorization": NimbaAUTH_TOKEN,
    "content-type": "application/json"
    } 
    payload = {
        "to": [num_phone],
        "sender_name": "convipre",
        "message": message
    }

    conn.request("POST", "/v1/messages", body=json.dumps(payload), headers=headers)

    res = conn.getresponse()
    data = res.read()

    print(data.decode("utf-8"))

def generate_otp():
   
     return str(random.randint(100000, 999999))




