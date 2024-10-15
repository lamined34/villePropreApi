from fastapi import Depends, HTTPException,status, APIRouter
from sqlalchemy.orm import Session
from typing import List
from database import get_db2
from models import *
from schemas import *
from utils import *
import models
import schemas


db = get_db2()

def get_villes():    
    villes = db.query(models.Ville).all()

    return villes


































def get_com_by_villes(id: int, db: Session = Depends(get_db)):    
    communes = db.query(models.Commune).filter(models.Commune.ville_id==id).all()
    return communes





