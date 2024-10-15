import httpx
import os
from typing import List
from dotenv import load_dotenv

# Charger les variables d'environnement depuis le fichier .env
load_dotenv()

NIMBA_API_URL = os.getenv("NIMBA_API_URL")
NIMBA_API_KEY = os.getenv("NIMBA_API_KEY")

from fastapi import FastAPI, HTTPException, Depends


from sqlalchemy.orm import Session
from datetime import datetime
import random
import os

# Importer les schémas et les modèles
from schemas import Phone, VerifyOTP
from models import OTP
from database import get_db  # Assurez-vous que vous avez une fonction get_db qui gère la session de la base de données

app = FastAPI()



# Initialiser le client Twilio


# Fonction pour générer un OTP
def generate_otp(length=6):
    return str(random.randint(100000, 999999))  # Génère un OTP de 6 chiffres

# Fonction pour envoyer l'OTP via Twilio
def send_otp(phone_number, otp):
    message = f"Your OTP is: {otp}"
    Nimba.messages.create(to=phone_number, from_="convipre", body=message)

# Endpoint pour envoyer l'OTP
@app.post("/send_otp/")
def send_otp_route(phone: Phone, db: Session = Depends(get_db)):
    otp = generate_otp()
    db_otp = db.query(OTP).filter(OTP.phone_number == phone.phone_number).first()
    if db_otp:
        db_otp.otp = otp
        db_otp.created_at = datetime.utcnow()
    else:
        db_otp = OTP(phone_number=phone.phone_number, otp=otp, created_at=datetime.utcnow())
        db.add(db_otp)
    db.commit()
    send_otp(phone.phone_number, otp)
    return {"detail": "OTP envoyé avec succès"}

# Endpoint pour vérifier l'OTP
@app.post("/verify_otp/")
def verify_otp_route(otp_data: VerifyOTP, db: Session = Depends(get_db)):
    db_otp = db.query(OTP).filter(OTP.phone_number == otp_data.phone_number).first()
    if not db_otp:
        raise HTTPException(status_code=400, detail="OTP non trouvé")
    if db_otp.otp != otp_data.otp:
        raise HTTPException(status_code=400, detail="OTP non valide")
    db.delete(db_otp)
    db.commit()
    return {"detail": "OTP vérifié avec succès"}