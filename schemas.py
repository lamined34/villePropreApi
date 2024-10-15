from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional, Union
from datetime import datetime, date



class Ville(BaseModel):
    id : int
    ville : str
    
    class Config:
        from_attributes = True

class Commune(BaseModel):
    id : int
    commune : str

    class Config:
        from_attributes = True
        
class QuartierOut(BaseModel):
    id: int
    quartier : str
    
    class Config:
        from_attributes = True


class SingleQuartier(QuartierOut):
    ville_id: int
    
    class Config:
        from_attributes = True
        
class Utilisateur(BaseModel):
    quartier_id : int
    nom_prenom : str
    tel : str
    genre : str
    email : EmailStr
    copie_pi : Optional[str] = None
    role: str
    create_at : datetime
    is_actif: bool
    update_at: datetime      
    
class UtilisateurBase(BaseModel):
    quartier_id : int
    nom_prenom : str
    tel : str
    genre : str
    email : EmailStr
    mot_de_passe: str
    copie_pi : Optional[str] = None
    role: str
    create_at : datetime
    is_actif: bool
    update_at: datetime
    

class UtilisateurCreate(UtilisateurBase):
    pass
    

class PmeCreate(UtilisateurCreate):
    nom_pme: str
    description: str
    zone_intervention: str
    num_enregistrement: str
    tarif_mensuel: int
    tarif_abonnement: int
    logo_pme: Optional[str] = None
    
class ClientCreate(BaseModel):
    num_rccm: Optional[str] = None
    nom_entreprise: Optional[str] = None
    
class UtilisateurOut(BaseModel):
    id: int
    quartier_id: int
    nom_prenom: str
    tel: str
    genre: str
    email: str
    copie_pi: str
    role: str
    create_at: datetime
    is_actif: bool
    update_at: datetime

    class Config:
        from_attributes = True


class UtilisateurLogin(BaseModel):
    email: EmailStr
    password : str


    
class PmeOut(BaseModel):
    id: int
    utilisateur: UtilisateurOut
    nom_pme: str
    description: str
    zone_intervention: str
    num_enregistrement: str
    tarif_mensuel: int
    tarif_abonnement: int
    logo_pme: str

    class Config:
        from_attributes = True
    
class ClientOut(BaseModel):
    id: int
    utilisateur: UtilisateurOut                                                                       
    num_rccm: Optional[str] = None
    nom_entreprise: Optional[str] = None

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    user_id: str | None = None
    role : str
    

class AbonnementBase(BaseModel):
    pme_id: int
    num_abonnement: str
    tarif_abonnement: int
    status_abonnement: str 
    debut_abonnement: datetime
    fin_abonnement: Optional[date]
   

class AbonnementCreate(AbonnementBase):
    pass

class AbonnementOut(AbonnementBase):
    id: int
    status_abonnement: str
    utilisateurs_id: int

    class Config:
        from_attributes = True
        from_attributes = True

class AbonneeOut(BaseModel):
    utilisateur : Union[UtilisateurOut, ClientOut]
    status_abonnement: str
    debut_abonnement: datetime

class ma_pme_out(BaseModel):
    pme: PmeOut


class UpdatePme(BaseModel):
    nom_pme: str
    description: str
    zone_intervention: str
    tarif_mensuel: int
    tarif_abonnement: int
    logo_pme: str   

class UpdatePassword(BaseModel):
    old_password: str
    new_password: str

# les schema pour la mise à jour du Client
class ClientUpdateBase(BaseModel):
    quartier_id: Optional[int] = None
    nom_prenom: Optional[str] = None
    tel: Optional[str] = None
    genre: Optional[str] = None
    email: Optional[EmailStr] = None
    copie_pi: Optional[str] = None
    is_actif: Optional[bool] = None
    num_rccm: Optional[str] = None
    nom_entreprise: Optional[str] = None

class EntrepriseClientUpdate(ClientUpdateBase):
    num_rccm: Optional[str] = None
    nom_entreprise: Optional[str] = None

class MenageClientUpdate(ClientUpdateBase):
    pass

class CommentIn(BaseModel):
    utilisateur_id: int
    pme_id: int
    message: str
    note: Optional[int]
    date_publicat: datetime

class CommentOut(BaseModel):
    message: str
    note: Optional[int]
    date_publicat: datetime

class Commentshow(BaseModel):
    message: str
    auteur: int
    note: Optional[int]
    date_publicat: datetime

