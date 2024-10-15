from fastapi import Depends, HTTPException,status, APIRouter
from sqlalchemy.orm import Session
from typing import List
from models import *
from database import get_db
from schemas import *
from utils import *

router = APIRouter(
    prefix="/commentaire",
    tags=["Commentaire"]
)



@router.post("/", response_model= CommentOut, tags=["Commentaire"])
def ajouter_commentaire(commentaire: CommentIn,
                        current_user: UtilisateurOut = Depends(role_required(["menage", "entreprise", "pme"])),
                        db: Session = Depends(get_db)):

    # Récupérer la PME associée à l'utilisateur s'il s'agit d'une PME
    pme_associee = db.query(Pme).filter(Pme.utilisateur_id == current_user.id).first()

    if current_user.role == "pme":
        # Vérifier si la PME essaie de commenter elle-même (utilisateur_id = celui de la PME)
        if commentaire.utilisateur_id == current_user.id:
            raise HTTPException(status_code=403, detail="Une PME ne peut pas se commenter elle-même.")
        
        # Vérifier si la PME commente sur un utilisateur (ménage ou entreprise) abonné à elle
        abonnement = db.query(Abonnement).filter(
            Abonnement.utilisateurs_id == commentaire.utilisateur_id,
            Abonnement.pme_id == pme_associee.id
        ).first()

        if not abonnement:
            raise HTTPException(status_code=403, detail="Vous ne pouvez commenter que les utilisateurs abonnés à votre PME.")
    
    else:
        # Si l'utilisateur est un ménage ou une entreprise
        # Vérifier s'il est abonné à la PME qu'il souhaite commenter
        abonnement = db.query(Abonnement).filter(
            Abonnement.utilisateurs_id == current_user.id,
            Abonnement.pme_id == commentaire.pme_id
        ).first()
        
        if not abonnement:
            raise HTTPException(status_code=403, detail="Vous devez être abonné à cette PME pour la commenter.")
        if current_user.id != commentaire.utilisateur_id :
            raise HTTPException(status_code=403, detail="Vous ne pouvez pas effectuer de commentaire")
    # Créer et sauvegarder le commentaire
    nouveau_commentaire = Commentaire(
        utilisateur_id=current_user.id if current_user.role != "pme" else commentaire.utilisateur_id,
        pme_id=commentaire.pme_id,
        message=commentaire.message,
        auteur=current_user.id,
        note=commentaire.note,
        date_publicat=commentaire.date_publicat
    )

    db.add(nouveau_commentaire)
    db.commit()
    db.refresh(nouveau_commentaire)

    return nouveau_commentaire

######################################################################################################
#                         L'affichage des commentaires des clients                                                #
######################################################################################################

@router.get("/{pme_id}", response_model=List[Commentshow], tags=["Commentaire"])
def afficher_commentaires(
    pme_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: UtilisateurOut = Depends(role_required(["menage", "entreprise"]))
):
    
    abonnement = db.query(Abonnement).filter(
                Abonnement.utilisateurs_id == current_user.id,
                Abonnement.pme_id == pme_id
            ).first()
    if not abonnement:
        raise HTTPException(status_code=403, detail="Vous devez être abonné à cette PME pour afficher les commentaires.")
    
    utilisateur_id = current_user.id
    # Vérifier si un filtre utilisateur est appliqué
    if utilisateur_id:
        commentaires = db.query(Commentaire).filter(
            Commentaire.utilisateur_id == utilisateur_id
        ).all()
        if not commentaires:
            raise HTTPException(status_code=404, detail="Aucun commentaire trouvé pour cet utilisateur.")

        
    return commentaires
######################################################################################################
#                         L'affichage des commentaires des Pmes                                                #
######################################################################################################
@router.get("/", response_model=List[Commentshow], tags=["Commentaire"])
def afficher_commentaires(
    utilisateur_id:Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: UtilisateurOut = Depends(role_required(["pme"]))
):
    """
    Affiche les commentaires des utilisateurs abonnés à la PME.
    """

    # Récupérer la PME associée à l'utilisateur actuel
    pme_associee = db.query(Pme).filter(Pme.utilisateur_id == current_user.id).first()

    # Vérifier si l'utilisateur (ménage ou entreprise) est abonné à la PME actuelle
    abonnement = db.query(Abonnement).filter(
        Abonnement.utilisateurs_id == utilisateur_id,
        Abonnement.pme_id == pme_associee.id
    ).first()

    if not abonnement:
        raise HTTPException(status_code=403, detail="Vous ne pouvez consulter que les commentaires des utilisateurs abonnés à votre PME.")

    # Récupérer les commentaires de l'utilisateur si l'abonnement existe
    commentaires = db.query(Commentaire).filter(
        Commentaire.utilisateur_id == utilisateur_id,
        Commentaire.pme_id == pme_associee.id
    ).all()

    if not commentaires:
        raise HTTPException(status_code=404, detail="Aucun commentaire trouvé pour cet utilisateur.")

    return commentaires

######################################################################################################
#                         L'affichage des commentaires des Pmes                                                #
######################################################################################################

@router.delete("/{comment_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Commentaire"])
def supprimer_commentaire(
    comment_id: int,
    db: Session = Depends(get_db),
    current_user: UtilisateurOut = Depends(role_required(["pme", "menage", "entreprise"]))
):
    
    # Vérifier si le commentaire existe et appartient à l'utilisateur actuel
        verif_comment = db.query(Commentaire).filter(
            Commentaire.auteur == current_user.id,
            Commentaire.id == comment_id
        ).first()

        if not verif_comment:
            raise HTTPException(status_code=404, detail="Aucun commentaire trouvé pour cet utilisateur.")
        # Supprimer le commentaire
        db.delete(verif_comment)
        db.commit()

        return None
