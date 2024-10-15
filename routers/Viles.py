from fastapi import Depends, HTTPException,status, APIRouter
from sqlalchemy.orm import Session
from typing import List
from models import *
from database import get_db
from schemas import *
from utils import *
import models
import schemas
import service.Villes as service

router = APIRouter(
    prefix="/vile",
    tags=["Villes"]
   
)


@router.get("/", response_model=List[schemas.Ville], tags=["Villes"])
def get_villes():
    return service.get_villes()






































@router.get("/{id}/communes", response_model=List[schemas.Commune], tags=["Villes"])
def get_com_by_villes(id: int, db: Session = Depends(get_db)):
    
    communes = db.query(models.Commune).filter(models.Commune.ville_id==id).all()
    
    return communes





