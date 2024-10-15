from fastapi import Depends, APIRouter
from sqlalchemy.orm import Session
from typing import List
from models import *
from database import get_db
from schemas import *
from utils import *


router = APIRouter(
    prefix="/commune",
    tags=["Communes"]
)


@router.get("/", response_model=List[Commune], tags=["Communes"])
def get_communes(db: Session = Depends(get_db)):
    
    communes = db.query(Commune).all()
    
    return communes

@router.get("/{id}/quartiers", response_model=List[QuartierOut], tags=["Communes"])
def get_quartiers_by_com(id:int, db: Session = Depends(get_db)):
    
    quartiers = db.query(Quartier).filter(Quartier.commune_id==id).all()
    
    return quartiers