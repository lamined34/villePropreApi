from fastapi import Depends, HTTPException, UploadFile, File, Form, status, APIRouter
#from con_vi_propre_api.main import UPLOAD_DIRECTORY_COPIE_PI
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import List
from models import *
from database import get_db
from schemas import *
from utils import *
import uuid

import service.Clients as service



router =  APIRouter(
    prefix="/client",
    tags=["Client"]
)

def get_clients_by_pme(db: Session, pme_id: int):
    return db.query(Client).join(Abonnement).filter(Abonnement.pme_id == pme_id).all()

######################################################################################################
#            Creation de compte pour les roles "menage" et "entreprise"                              #
######################################################################################################
@router.post("/", status_code=status.HTTP_201_CREATED,response_model=Union[ClientOut, UtilisateurOut], tags=["Client"])
async def create_client(
    quartier_id: int = Form(...),
    nom_prenom: str = Form(...),
    tel: str = Form(...),
    genre: str = Form(...),
    email: str = Form(...),
    mot_de_passe: str = Form(...),
    copie_pi: UploadFile = File(...),
    role: str = Form(...),
    create_at: datetime = Form(...),
    update_at: datetime = Form(...),
    is_actif: bool = Form(...),
    num_rccm: Optional[str] = Form(None),
    nom_entreprise: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    return service.create_client(quartier_id, nom_prenom, genre, email, mot_de_passe, copie_pi,
                                 role, create_at, update_at, is_actif, num_rccm, nom_entreprise,
                                 db)



























######################################################################################################
#            Affichage des informations du clients                                                   #
######################################################################################################           
@router.get("/", response_model=List[ClientOut], tags=['Client'])
def get_clients(db: Session = Depends(get_db)):
    # Requête pour obtenir tous les utilisateurs avec une jointure externe sur Client
    utilisateurs = db.query(Utilisateur).outerjoin(Client, Client.utilisateur_id==Utilisateur.id).filter(
        or_(Utilisateur.role == "entreprise", Utilisateur.role == "menage")
    ).all()

    # Transformer les résultats en format approprié
    client_list = []
    for utilisateur in utilisateurs:
        # Vérifier s'il y a des clients associés
        client = utilisateur.clients[0] if utilisateur.clients else None
        
        client_data = ClientOut(
            id=client.id if client else utilisateur.id,
            utilisateur=UtilisateurOut(
                id=utilisateur.id,
                quartier_id=utilisateur.quartier_id,
                nom_prenom=utilisateur.nom_prenom,
                tel=utilisateur.tel,
                genre=utilisateur.genre,
                email=utilisateur.email,
                copie_pi=utilisateur.copie_pi,
                role=utilisateur.role,
                create_at=utilisateur.create_at,
                is_actif=utilisateur.is_actif,
                update_at=utilisateur.update_at,
            ),
            num_rccm=client.num_rccm if client else None,
            nom_entreprise=client.nom_entreprise if client else None
        )
        client_list.append(client_data)

    return client_list


######################################################################################################
#                     Affichage des informations du clients                                          #
###################################################################################################### 
@router.get('/{client_role}/{client_id}', response_model=Union[ClientOut, UtilisateurOut], tags=["Client"])
def get_client(client_role: str, client_id: int, db: Session = Depends(get_db)):
    # Vérification du rôle du client
    if client_role not in ["menage", "entreprise"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Vous ne pouvez afficher que les informations concernant un client de type menage ou entreprise!"
        )

    # Requête pour récupérer les informations de l'utilisateur
    utilisateur = db.query(Utilisateur).filter(Utilisateur.id == client_id).first()

    # Si l'utilisateur n'existe pas ou si le rôle est "pme", lever une exception
    if utilisateur is None or utilisateur.role != client_role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Aucun client ne correspond à vos paramètres de recherches"
        )

    # Si le rôle est "entreprise", joindre avec la table Client
    if client_role == "entreprise":
        client = db.query(Client).filter(Client.utilisateur_id == utilisateur.id).first()

        if client is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Aucun client ne correspond à vos paramètres de recherches"
            )

        return ClientOut(
            id=client.id,
            utilisateur=UtilisateurOut(
                id=utilisateur.id,
                quartier_id=utilisateur.quartier_id,
                nom_prenom=utilisateur.nom_prenom,
                tel=utilisateur.tel,
                genre=utilisateur.genre,
                email=utilisateur.email,
                copie_pi=utilisateur.copie_pi,
                role=utilisateur.role,
                create_at=utilisateur.create_at,
                is_actif=utilisateur.is_actif,
                update_at=utilisateur.update_at,
            ),
            num_rccm=client.num_rccm,
            nom_entreprise=client.nom_entreprise
        )

    # Pour les rôles autres que "entreprise", retourner uniquement les informations utilisateur
    return UtilisateurOut(
            id=utilisateur.id,
            quartier_id=utilisateur.quartier_id,
            nom_prenom=utilisateur.nom_prenom,
            tel=utilisateur.tel,
            genre=utilisateur.genre,
            email=utilisateur.email,
            copie_pi=utilisateur.copie_pi,
            role=utilisateur.role,
            create_at=utilisateur.create_at,
            is_actif=utilisateur.is_actif,
            update_at=utilisateur.update_at,
        )
    

@router.get('/nom_ou_tel/{client_role}/{nom_prenom}/{nom_entreprise}/{tel}', response_model=Union[ClientOut, UtilisateurOut], tags=["Client"])
def search_client(client_role: str, search_value: Optional[str]=None, db: Session = Depends(get_db)):
    # Vérification du rôle du client
    if client_role not in ["menage", "entreprise"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Vous ne pouvez rechercher que les informations concernant un client de type menage ou entreprise!"
        )

    # Requête pour récupérer les informations de l'utilisateur
    if client_role == "menage":
        utilisateur = db.query(Utilisateur).filter(
            or_(Utilisateur.nom_prenom.contains(search_value), Utilisateur.tel.contains(search_value), Utilisateur.email.contains(search_value))
        ).first()
    elif client_role == "entreprise":
        client = db.query(Client).join(Utilisateur).filter(
            or_(Client.nom_entreprise.contains(search_value), Utilisateur.tel.contains(search_value), Utilisateur.email.contains(search_value), Utilisateur.nom_prenom.contains(search_value))
        ).first()
        
        if client:
            utilisateur = client.utilisateur

    # Si aucun utilisateur ou client n'est trouvé, lever une exception
    if not utilisateur:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Aucun client ne correspond à vos paramètres de recherches"
        )

    # Si le rôle est "entreprise", retourner les informations du client entreprise
    if client_role == "entreprise" and client:
        return ClientOut(
            id=client.id,
            utilisateur=UtilisateurOut(
                id=utilisateur.id,
                quartier_id=utilisateur.quartier_id,
                nom_prenom=utilisateur.nom_prenom,
                tel=utilisateur.tel,
                genre=utilisateur.genre,
                email=utilisateur.email,
                copie_pi=utilisateur.copie_pi,
                role=utilisateur.role,
                create_at=utilisateur.create_at,
                is_actif=utilisateur.is_actif,
                update_at=utilisateur.update_at,
            ),
            num_rccm=client.num_rccm,
            nom_entreprise=client.nom_entreprise
        )

    # Pour les rôles autres que "entreprise", retourner uniquement les informations utilisateur
    return UtilisateurOut(
            id=utilisateur.id,
            quartier_id=utilisateur.quartier_id,
            nom_prenom=utilisateur.nom_prenom,
            tel=utilisateur.tel,
            genre=utilisateur.genre,
            email=utilisateur.email,
            copie_pi=utilisateur.copie_pi,
            role=utilisateur.role,
            create_at=utilisateur.create_at,
            is_actif=utilisateur.is_actif,
            update_at=utilisateur.update_at,
        )
    

@router.put("/{utilisateur_id}/{role}", response_model=ClientOut, tags=["Client"])
def update_client(utilisateur_id: int, role: str, client_data: Union[MenageClientUpdate, EntrepriseClientUpdate], db: Session = Depends(get_db)):
    # Vérifier si le rôle est valide
    if role not in ["menage", "entreprise"]:
        raise HTTPException(status_code=400, detail="Rôle invalide. Les rôles valides sont 'menage' ou 'entreprise'.")

    # Rechercher l'utilisateur existant par ID
    utilisateur = db.query(Utilisateur).filter(Utilisateur.id == utilisateur_id).first()
    if not utilisateur:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé")

    # Vérifier si le rôle de l'utilisateur correspond
    if utilisateur.role != role:
        raise HTTPException(status_code=400, detail="Le rôle de l'utilisateur ne correspond pas à celui fourni dans l'URL.")

    # Mise à jour des champs de l'utilisateur
    for field, value in client_data.dict(exclude_unset=True).items():
        if hasattr(utilisateur, field) and field not in ['num_rccm', 'nom_entreprise']:
            setattr(utilisateur, field, value)

    # Si le rôle est "entreprise", récupérer le client associé et mettre à jour les champs spécifiques
    if role == "entreprise":
        # Récupérer le client lié à l'utilisateur
        client = db.query(Client).filter(Client.utilisateur_id == utilisateur_id).first()
        if not client:
            raise HTTPException(status_code=404, detail="Client entreprise non trouvé")

        # Mettre à jour les champs spécifiques de l'entreprise
        if client_data.num_rccm is not None:
            client.num_rccm = client_data.num_rccm
        if client_data.nom_entreprise is not None:
            client.nom_entreprise = client_data.nom_entreprise

        # Ajouter le client à la session
        db.add(client)

    # Sauvegarder les modifications de l'utilisateur
    db.add(utilisateur)
    db.commit()

    # Rafraîchir les objets pour refléter les mises à jour
    db.refresh(utilisateur)
    if role == "entreprise":
        db.refresh(client)

    # Préparer la réponse de mise à jour
    updated_client = ClientOut(
        id=utilisateur.id,
        utilisateur=UtilisateurOut(
            id=utilisateur.id,
            quartier_id=utilisateur.quartier_id,
            nom_prenom=utilisateur.nom_prenom,
            tel=utilisateur.tel,
            genre=utilisateur.genre,
            email=utilisateur.email,
            copie_pi=utilisateur.copie_pi,
            role=utilisateur.role,
            create_at=utilisateur.create_at,
            is_actif=utilisateur.is_actif,
            update_at=utilisateur.update_at,
        ),
        num_rccm=client.num_rccm if role == 'entreprise' else None,
        nom_entreprise=client.nom_entreprise if role == 'entreprise' else None
    )

    return updated_client

@router.put("/{user_id}/update-password", tags=["Client"])
def update_password(user_id: int, password_data: UpdatePassword, db: Session = Depends(get_db)):
    # Récupérer l'utilisateur de la base de données
    user = db.query(Utilisateur).filter(Utilisateur.id == user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Utilisateur non trouvé"
        )

    # Vérifier que l'ancien mot de passe est correct
    if not verify_password(password_data.old_password, user.mot_de_passe):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="L'ancien mot de passe est incorrect"
        )

    # Hacher le nouveau mot de passe et le mettre à jour dans la base de données
    user.mot_de_passe = hash_password(password_data.new_password)
    db.commit()
    db.refresh(user)

    return {"detail": "Mot de passe mis à jour avec succès"}