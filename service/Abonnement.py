from fastapi import  Depends, HTTPException, status, APIRouter
from sqlalchemy.orm import Session
from typing import List
from models import *
from database import get_db
from schemas import *
from utils import *






######################################################################################################
#                     creation d'un abonnement                                                       #
######################################################################################################
async def create_abonnement(
    abonnement: AbonnementCreate,
    current_user: UtilisateurOut = Depends(role_required(["menage", "entreprise"])),
    db: Session = Depends(get_db)
):
    # Si l'utilisateur a le rôle "entreprise", vérifier qu'il est dans la table client
    if current_user.role == "entreprise":
        client = db.query(Client).filter(Client.utilisateur_id == current_user.id).first()
        if not client:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="L'utilisateur entreprise n'est pas enregistré comme client."
            )
     # Vérifier que l'utilisateur ne peut pas souscrire deux fois à la même PME
    existing_abonnement = db.query(Abonnement).filter(
        Abonnement.utilisateurs_id == current_user.id,
        Abonnement.pme_id == abonnement.pme_id
    ).first()
    
    if existing_abonnement:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Vous avez déjà souscrit à un abonnement auprès de cette PME."
        )
    
    # Vérifier que l'utilisateur ne peut pas souscrire à plusieurs PME différentes
    existing_abonnements = db.query(Abonnement).filter(
        Abonnement.utilisateurs_id == current_user.id
    ).all()
    
    if existing_abonnements:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Vous ne pouvez souscrire qu'à une seule PME."
        )
    pme = db.query(Pme).outerjoin(Utilisateur, Pme.utilisateur_id==Utilisateur.id).filter(Pme.id == abonnement.pme_id).first()

    # Créer l'abonnement
    new_abonnement = Abonnement(
        utilisateurs_id=current_user.id,
        pme_id=abonnement.pme_id,
        num_abonnement=abonnement.num_abonnement,
        tarif_abonnement=abonnement.tarif_abonnement,
        status_abonnement="En attente",
        debut_abonnement=abonnement.debut_abonnement,
        fin_abonnement=abonnement.fin_abonnement,
    )

    if pme:
        message = f"Salut! nouvelle demande d'abonnement de {current_user.nom_prenom} en tant que {current_user.role} au numero d'abonnement{new_abonnement.num_abonnement}. Veuillez valider svp!."
        envoie_sms(pme.utilisateur.tel, message)

    db.add(new_abonnement)
    db.commit()
    db.refresh(new_abonnement)

    return new_abonnement
    


async def get_pme_abonnee(
    current_user: UtilisateurOut = Depends(role_required(["menage", "entreprise"])),
    db: Session = Depends(get_db)
):
    # Récupérer l'abonnement actif de l'utilisateur connecté 
    abonnement = db.query(Abonnement).filter(
        Abonnement.utilisateurs_id == current_user.id
        #Abonnement.status_abonnement == "Actif"             #l'abonnement doit être "Actif"
    ).first()

    if not abonnement:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Aucun abonnement actif trouvé pour cet utilisateur."
        )

    # Récupérer les informations de la PME liée à cet abonnement
    pme = db.query(Pme).filter(Pme.id == abonnement.pme_id).first()

    if not pme:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="La PME liée à cet abonnement n'a pas été trouvée."
        )

    return pme


async def get_abonnements_by_pme(
    utilisateur_id: int,
    current_user: UtilisateurOut = Depends(role_required(["pme"])),
    db: Session = Depends(get_db)
):
    
    if utilisateur_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Vous n'êtes pas autorisé à acceder à ses informations"
        )
    
    
    abonnes = db.query(Abonnement).outerjoin(
        Pme, Abonnement.pme_id == Pme.id).outerjoin(Utilisateur, Abonnement.utilisateurs_id==Utilisateur.id).filter(
        Pme.utilisateur_id == current_user.id).all()
    
       

    if not abonnes:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Aucun abonnement trouvé pour la PME avec l'ID spécifié."
        )
    
    abonne_list = []
    for abonne in abonnes:
        if abonne.utilisateur.role == "entreprise":
            for client in abonne.utilisateur.clients:
                client_id = client.id
                num_rccm = client.num_rccm
                nom_entreprise = client.nom_entreprise
            list_abonne_entreprise =  AbonneeOut(
                    utilisateur = ClientOut(
                        id = client_id,
                        utilisateur = UtilisateurOut(
                            id = abonne.utilisateur.id,
                            quartier_id = abonne.utilisateur.quartier_id,
                            nom_prenom = abonne.utilisateur.nom_prenom,
                            tel= abonne.utilisateur.tel,
                            genre = abonne.utilisateur.genre,
                            email = abonne.utilisateur.email,
                            copie_pi = abonne.utilisateur.copie_pi,
                            role = abonne.utilisateur.role,
                            create_at = abonne.utilisateur.create_at,
                            is_actif = abonne.utilisateur.is_actif,
                            update_at = abonne.utilisateur.update_at
                        ) ,                                                                      
                        num_rccm = num_rccm,
                        nom_entreprise = nom_entreprise
                    ),
                    status_abonnement= abonne.status_abonnement,
                    num_abonnement = abonne.num_abonnement,
                    debut_abonnement = abonne.debut_abonnement,
                    fin_abonnement = abonne.fin_abonnement)
            if list_abonne_entreprise not in abonne_list:
                abonne_list.append(list_abonne_entreprise)

        if abonne.utilisateur.role == "menage":
            list_abonne_menage = AbonneeOut(
                utilisateur = UtilisateurOut(
                        id = abonne.utilisateur.id,
                        quartier_id = abonne.utilisateur.quartier_id,
                        nom_prenom = abonne.utilisateur.nom_prenom,
                        tel= abonne.utilisateur.tel,
                        genre = abonne.utilisateur.genre,
                        email = abonne.utilisateur.email,
                        copie_pi = abonne.utilisateur.copie_pi,
                        role = abonne.utilisateur.role,
                        create_at = abonne.utilisateur.create_at,
                        is_actif = abonne.utilisateur.is_actif,
                        update_at = abonne.utilisateur.update_at
                ),    
                status_abonnement= abonne.status_abonnement,
                num_abonnement = abonne.num_abonnement,
                debut_abonnement = abonne.debut_abonnement,
                fin_abonnement = abonne.fin_abonnement)

            if list_abonne_menage not in abonne_list:
                abonne_list.append(list_abonne_menage)    
            

    return abonne_list


def update_abonnement_status(
    abonnement_id: int, 
    confirmation_message: str,
    current_user: UtilisateurOut = Depends(role_required(["pme"])),
    db: Session = Depends(get_db)
    ):
    # Vérification des valeurs de confirmation_message
    if confirmation_message not in ["accepted", "rejected"]:
        raise HTTPException(status_code=400, detail="Invalid confirmation message")

    # Récupération de l'abonnement par ID
    abonnement = db.query(Abonnement).filter(Abonnement.id == abonnement_id).first()
    if not abonnement:
        raise HTTPException(status_code=404, detail="Abonnement non trouvé")

    # Mise à jour du statut de l'abonnement
    if confirmation_message == "accepted":
        abonnement.status_abonnement = "actif"
    else:
        abonnement.status_abonnement = "rejected"  # Assurez-vous que ce soit la valeur correcte pour "rejected"

    # Sauvegarde des changements dans la base de données
    db.commit()

    return {"message": "Abonnement mis à jour avec succès", "id": abonnement_id, "nouveau_statut": abonnement.status_abonnement}



