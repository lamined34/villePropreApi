from fastapi import Depends, HTTPException,status, APIRouter
from sqlalchemy.orm import Session
from typing import List
from models import *
from database import get_db
from schemas import *
from utils import *
import models
import schemas


router = APIRouter(
    prefix="/quartier",
    tags=["Quartier"]
)


@router.get("/", response_model=List[schemas.QuartierOut], tags=["Quartier"])
def get_quartier(db: Session = Depends(get_db)):
    
    quartiers = db.query(models.Quartier).all()
    
    return quartiers

@router.get("/{quartier_id}", response_model=schemas.QuartierOut, tags=["Quartier"])
def get_quartier(quartier_id: int, db: Session = Depends(get_db)):
    
    quartier = db.query(models.Quartier).filter(models.Quartier.id == quartier_id).first()
    
    if quartier is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Il n'y a pas de quartier qui correspond à l'id fourni")
    
    return quartier