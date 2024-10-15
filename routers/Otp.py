from fastapi import  Depends, HTTPException, status, APIRouter
from sqlalchemy.orm import Session
from models import *
from database import get_db

from schemas import *
from utils import *

router = APIRouter(
    prefix="/otp",
    tags=["OTP"]
)


@router.post("/", tags=["OTP"])
async def verifier_otp(
    utilisateur_id: int,
    otp_code: str,
    db: Session = Depends(get_db)
):
    otp_record = db.query(OTP).filter(
        OTP.utilisateur_id == utilisateur_id,
        OTP.otp_code == otp_code,
        OTP.expiration_time >= datetime.utcnow()
    ).first()
    
    if not otp_record:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="OTP invalide ou expiré."
        )
    
    # Marquer l'utilisateur comme actif
    utilisateur = db.query(Utilisateur).filter(Utilisateur.id == utilisateur_id).first()
    utilisateur.is_actif = True
    db.commit()

    # Supprimer l'OTP après validation
    db.delete(otp_record)
    db.commit()
    
    return {"message": "Utilisateur activé avec succès."}