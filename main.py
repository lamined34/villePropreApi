import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.staticfiles import StaticFiles
from models import *
from database import engine, Base 
from schemas import *
from fastapi import FastAPI
from routers.Abonnement import router as abonnement_router
from routers.Auth import router as auth_router
from routers.Commentaire import router as commentaire_router
from routers.Otp import router as otp_router
from routers.Pmes import router as pmes_router
from routers.Viles import router as villes_router
from routers.Clients import router as client_router
from routers.Communes import router as commune_router
from routers.Quartiers import router as quartier_router



Base.metadata.create_all(bind=engine)

app = FastAPI()


app.mount("/static", StaticFiles(directory="static/Uploads"), name="uploads")
# dossiers de destination pour les uploads
UPLOAD_DIRECTORY_COPIE_PI = "static/uploads/copie_pi"
UPLOAD_DIRECTORY_LOGO_PME = "static/uploads/logo_pme"

# Verifier l'existence des dossiers
os.makedirs(UPLOAD_DIRECTORY_COPIE_PI, exist_ok=True)
os.makedirs(UPLOAD_DIRECTORY_LOGO_PME, exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(abonnement_router)
app.include_router(auth_router)
app.include_router(commentaire_router)
app.include_router(otp_router)
app.include_router(pmes_router)
app.include_router(villes_router)
app.include_router(client_router)
app.include_router(commune_router)
app.include_router(quartier_router)


@app.get('/')
def index_root():
    return {"message": "Bienvenue sur l'interface de developpement de conakry ville propre"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run('main:app', reload=True)



   






     





    




