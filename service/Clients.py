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



def get_clients_by_pme(db: Session, pme_id: int):
    return db.query(Client).join(Abonnement).filter(Abonnement.pme_id == pme_id).all()

######################################################################################################
#            Creation de compte pour les roles "menage" et "entreprise"                              #
######################################################################################################
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
    # Vérifier si l'email ou le numéro de téléphone existe déjà
    existing_user = db.query(Utilisateur).filter(
        (Utilisateur.email == email) | (Utilisateur.tel == tel)
    ).first()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="L'email ou le numéro de téléphone existe déjà dans la base de données."
        )

    # Hasher le mot de passe
    hashed_password = hash_password(mot_de_passe)

    # Sauvegarde du fichier copie_pi
    copie_pi_file_name = f"{uuid.uuid4()}_{copie_pi.filename}"
    copie_pi_file_path = os.path.join(UPLOAD_DIRECTORY_COPIE_PI, copie_pi_file_name)

    with open(copie_pi_file_path, "wb") as buffer:
        buffer.write(await copie_pi.read())

    # Création de l'utilisateur
    db_utilisateur = Utilisateur(
        quartier_id=quartier_id,
        nom_prenom=nom_prenom,
        tel=tel,
        genre=genre,
        email=email,
        mot_de_passe=hashed_password,
        copie_pi=copie_pi_file_name,
        role=role,
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

    # Vérifier si le role est 'entreprise' et stocker les informations dans la table 'clients'
    if role == "entreprise" and nom_entreprise:
        db_client = Client(
            utilisateur_id=db_utilisateur.id,
            num_rccm=num_rccm,
            nom_entreprise=nom_entreprise
        )
        db.add(db_client)
        db.commit()
        db.refresh(db_client)

        client_data = ClientOut(
            id=db_client.id,
            utilisateur=db_utilisateur,
            num_rccm=db_client.num_rccm,
            nom_entreprise=db_client.nom_entreprise
        )
        return client_data
    else:
        # Si le role est formater les informations de clients selon UtilisateurOut
        if role == "menage":
            user_data = UtilisateurOut(
                  id=db_utilisateur.id,
                  quartier_id=db_utilisateur.quartier_id,
                  nom_prenom=db_utilisateur.nom_prenom,
                  tel=db_utilisateur.tel,
                  genre=db_utilisateur.genre,
                  email=db_utilisateur.email,
                  copie_pi=db_utilisateur.copie_pi,
                  role=db_utilisateur.role,
                  create_at=db_utilisateur.create_at,
                  is_actif=db_utilisateur.is_actif,
                  update_at=db_utilisateur.update_at
            )
            return user_data
        else:
            raise HTTPException(
                 status_code=status.HTTP_400_BAD_REQUEST,
                 detail="Le rôle doit être 'menage' si ce n'est pas un client entreprise."
            )


######################################################################################################
#            Affichage des informations du clients                                                   #
######################################################################################################   
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