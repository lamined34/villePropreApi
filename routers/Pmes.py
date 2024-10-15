import uuid
from fastapi import Depends, HTTPException, UploadFile, File, Form, status, APIRouter
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import List
#from villePropreApi import UPLOAD_DIRECTORY_COPIE_PI, UPLOAD_DIRECTORY_LOGO_PME
from models import *
from database import get_db
from schemas import *
from utils import *


router = APIRouter(
    prefix="/pme",
    tags=["Pme"]
)

@router.post("/", status_code=status.HTTP_201_CREATED, response_model=PmeOut, tags=["Pme"])
async def register_pme(
    quartier_id: int = Form(...),
    nom_prenom: str = Form(...),
    tel: str = Form(...),
    genre: str = Form(...),
    email: str = Form(...),
    mot_de_passe: str = Form(...),
    copie_pi: UploadFile = File(...),
    create_at: datetime = Form(...),
    update_at: datetime = Form(...),
    is_actif: bool = Form(...),
    nom_pme: str = Form(...),
    description: str = Form(...),
    zone_intervention: str = Form(...),
    num_enregistrement: str = Form(...),
    tarif_mensuel: int = Form(...),
    tarif_abonnement: int = Form(...),
    logo_pme: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    # Vérifier si l'email ou le numéro de téléphone existe déjà
    existing_user = db.query(Utilisateur).filter(
        (Utilisateur.email == email) | (Utilisateur.tel == tel)
    ).first()
    existing_pme = db.query(Pme).filter(
        (Pme.nom_pme == nom_pme) | (Pme.num_enregistrement == num_enregistrement)
    ).first()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="L'email ou le numéro de téléphone existe déjà dans la base de données."
        )
    if existing_pme:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"La pme ou le numéro d'enregistrement existe déjà dans le système"
        )
    
    
    # Hasher le mot de passe
    hashed_password = hash_password(mot_de_passe)

    # Sauvegarde du fichier copie_pi
    copie_pi_file_name = f"{uuid.uuid4()}_{copie_pi.filename}"
    copie_pi_file_path = os.path.join(UPLOAD_DIRECTORY_COPIE_PI, copie_pi_file_name)

    with open(copie_pi_file_path, "wb") as buffer:
        buffer.write(await copie_pi.read())

    # Sauvegarde du fichier logo_pme
    logo_pme_file_name = f"{uuid.uuid4()}_{logo_pme.filename}"
    logo_pme_file_path = os.path.join(UPLOAD_DIRECTORY_LOGO_PME, logo_pme_file_name)

    with open(logo_pme_file_path, "wb") as buffer:
        buffer.write(await logo_pme.read())


    copie_pi_url = f"/static/uploads/copie_pi/{copie_pi_file_name}"
    logo_pme_url = f"/static/uploads/logo_pme/{logo_pme_file_name}"

    # Création de l'utilisateur
    db_utilisateur = Utilisateur(
        quartier_id=quartier_id,
        nom_prenom=nom_prenom,
        tel=tel,
        genre=genre,
        email=email,
        mot_de_passe=hashed_password,
        copie_pi=copie_pi_url,
        role="pme",
        create_at=create_at,
        is_actif=False,
        update_at=update_at,
    )
    db.add(db_utilisateur)
    db.commit()
    db.refresh(db_utilisateur)
    
    otp_code = generate_otp()
    expiration_time = datetime.utcnow() + timedelta(minutes=10)  # OTP valide pour 10 minutes
    
    new_otp = OTP(
        utilisateur_id=db_utilisateur.id,
        otp_code=otp_code,
        expiration_time=expiration_time
    )
    db.add(new_otp)
    db.commit()

    # Envoyer l'OTP par SMS ou email
    message = f"Votre code de validation est {otp_code}. Il est valable pour 10 minutes."
    envoie_sms(db_utilisateur.tel, message)
    

    # Création de l'entité PME
    db_pme = Pme(
        utilisateur_id=db_utilisateur.id,
        nom_pme=nom_pme,
        description=description,
        zone_intervention=zone_intervention,
        num_enregistrement=num_enregistrement,
        tarif_mensuel=tarif_mensuel,
        tarif_abonnement=tarif_abonnement,
        logo_pme=logo_pme_url,
    )
    db.add(db_pme)
    db.commit()
    db.refresh(db_pme)

    # Convertir en dictionnaire pour la réponse
    pme_data = {
        "id": db_pme.id,
        "utilisateur": {
            "id": db_utilisateur.id,
            "quartier_id": db_utilisateur.quartier_id,
            "nom_prenom": db_utilisateur.nom_prenom,
            "tel": db_utilisateur.tel,
            "genre": db_utilisateur.genre,
            "email": db_utilisateur.email,
            "copie_pi": db_utilisateur.copie_pi,
            "role": db_utilisateur.role,
            "create_at": db_utilisateur.create_at.isoformat(),
            "is_actif": db_utilisateur.is_actif,
            "update_at": db_utilisateur.update_at.isoformat(),
        },
        "nom_pme": db_pme.nom_pme,
        "description": db_pme.description,
        "zone_intervention": db_pme.zone_intervention,
        "num_enregistrement": db_pme.num_enregistrement,
        "tarif_mensuel": db_pme.tarif_mensuel,
        "tarif_abonnement": db_pme.tarif_abonnement,
        "logo_pme": db_pme.logo_pme,
    }

   
    # Utiliser `parse_obj` pour créer l'instance Pydantic
    pme_out = PmeOut(**pme_data)

    return pme_out


@router.get('/', response_model=List[PmeOut], tags=['Pme'])
def get_pmes(search_value: Optional[str]=None,db : Session = Depends(get_db)):
    
    if search_value:
        pmes = db.query(Pme).outerjoin(Utilisateur).filter(or_(Pme.nom_pme.contains(search_value), Utilisateur.nom_prenom.contains(search_value), Utilisateur.tel.contains(search_value), Utilisateur.email.contains(search_value))).all()
    else:
        pmes = db.query(Pme).outerjoin(Utilisateur).all()
     
        
    pme_list = []
    for pme in pmes:
        pme_data = PmeOut(
            id=pme.id,
            utilisateur=UtilisateurOut(
                id=pme.utilisateur.id,
                quartier_id=pme.utilisateur.quartier_id,
                nom_prenom=pme.utilisateur.nom_prenom,
                tel=pme.utilisateur.tel,
                genre=pme.utilisateur.genre,
                email=pme.utilisateur.email,
                mot_de_passe=pme.utilisateur.mot_de_passe,
                copie_pi=pme.utilisateur.copie_pi,
                role=pme.utilisateur.role,
                create_at=pme.utilisateur.create_at,
                is_actif=pme.utilisateur.is_actif,
                update_at=pme.utilisateur.update_at,
            ),
            nom_pme=pme.nom_pme,
            description=pme.description,
            zone_intervention=pme.zone_intervention,
            num_enregistrement=pme.num_enregistrement,
            tarif_mensuel=pme.tarif_mensuel,
            tarif_abonnement=pme.tarif_abonnement,
            logo_pme=pme.logo_pme
        )
        pme_list.append(pme_data)

    return pme_list



@router.get('/id/{pme_id}', response_model=PmeOut, tags=['Pme'])
def get_pme(pme_id: int,  db: Session = Depends(get_db)):
    # Requête pour récupérer les données de la PME avec les informations utilisateur associées
    pme = db.query(Pme).outerjoin(Utilisateur).filter(Pme.id == pme_id).first()
    
    if pme is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="L'id fourni ne correspond à aucune Pme")

    # Transformation en format approprié
    pme_data = PmeOut(
        id=pme.id,
        utilisateur=UtilisateurOut(
            id=pme.utilisateur.id,
            quartier_id=pme.utilisateur.quartier_id,
            nom_prenom=pme.utilisateur.nom_prenom,
            tel=pme.utilisateur.tel,
            genre=pme.utilisateur.genre,
            email=pme.utilisateur.email,
            mot_de_passe=pme.utilisateur.mot_de_passe,
            copie_pi=pme.utilisateur.copie_pi,
            role=pme.utilisateur.role,
            create_at=pme.utilisateur.create_at,
            is_actif=pme.utilisateur.is_actif,
            update_at=pme.utilisateur.update_at,
        ),
        nom_pme=pme.nom_pme,
        description=pme.description,
        zone_intervention=pme.zone_intervention,
        num_enregistrement=pme.num_enregistrement,
        tarif_mensuel=pme.tarif_mensuel,
        tarif_abonnement=pme.tarif_abonnement,
        logo_pme=pme.logo_pme
    )

    return pme_data

@router.get('/pmes/recherche', response_model=list[PmeOut], tags=['Pme'])
def get_pme( search_value= Optional[str], db: Session = Depends(get_db)):
    # Requête pour récupérer les données de la PME avec les informations utilisateur associées
    pme = db.query(Pme).outerjoin(Utilisateur).filter(or_(Pme.nom_pme.contains(search_value), Utilisateur.nom_prenom.contains(search_value), Utilisateur.tel.contains(search_value), Utilisateur.email.contains(search_value))).all()
    
    if pme is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Le nom fourni ne correspond à aucune Pme")

    return pme

@router.put("/pmes/{pme_id}", response_model=UpdatePme, tags=["Pme"])
async def update_pme(pme_id: int, pme: UpdatePme, db: Session = Depends(get_db)):
    # Récupérer la PME existante de la base de données
    db_pme = db.query(Pme).filter(Pme.id == pme_id).first()
    
    if not db_pme:
        raise HTTPException(status_code=404, detail="PME non trouvée")

    # Mise à jour des champs de la PME
    db_pme.nom_pme = pme.nom_pme
    db_pme.description = pme.description
    db_pme.zone_intervention = pme.zone_intervention
    db_pme.tarif_mensuel = pme.tarif_mensuel
    db_pme.tarif_abonnement = pme.tarif_abonnement
    db_pme.logo_pme = pme.logo_pme

    # Enregistrement des modifications dans la base de données
    db.commit()
    db.refresh(db_pme)
    
    return db_pme