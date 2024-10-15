from fastapi import Depends, HTTPException,status, APIRouter
from sqlalchemy.orm import Session
from typing import List
from models import *
from database import get_db
from schemas import *
from utils import *
import models
import schemas

import data.Villes as data



def get_villes():  
    return data.get_villes()




























def get_com_by_villes(id: int, db: Session = Depends(get_db)):    
    communes = db.query(models.Commune).filter(models.Commune.ville_id==id).all()
    return communes





