from fastapi import Depends, HTTPException, status, APIRouter
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from models import *
from database import get_db
from schemas import *
from utils import *

router = APIRouter(
    prefix="/Authentification",
    tags=["Authentification"]
)


######################################################################################################
#                    Authentification                                                                #
###################################################################################################### 
@router.post("/", tags=["Authentification"])
def login_user(user_access: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    
    user = db.query(Utilisateur).filter(Utilisateur.email == user_access.username).first()
    
    if not user :
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Les accès fournis sont incorrects"
        )
    
    if not verify_password(user_access.password, user.mot_de_passe):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Le mot de passe fourni n'est pas le bon"
        )
    access_token = create_access_token(data={"user_id":user.id, "role":user.role})
    return {
        "user_id":user.id,
        "access_token": access_token,
        "token_type": "bearer"
    }
