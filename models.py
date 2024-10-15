from datetime import datetime
from email import message
from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, DateTime, Text
from sqlalchemy.orm import relationship
from database import Base


##===============================================================##
##                       ADRESSE                                 ##
##===============================================================##

############################
#        Table Ville       #
############################
class Ville(Base):
    __tablename__ = "villes"
    
    id = Column(
        Integer,
        primary_key=True,
        nullable=False
    )
    ville = Column(
        String,
        nullable=False
    )
    
    communes = relationship(
        "Commune",
        backref="ville"
    )
    __table_args__ = {'extend_existing': True}

############################
#        Table Commune     #
############################
class Commune(Base):
    __tablename__ = "communes"
    
    id = Column(
        Integer,
        primary_key=True,
        nullable=False
    )
    ville_id = Column(
        Integer,
        ForeignKey("villes.id"),
        nullable=False
    )
    commune = Column(
        String,
        nullable=False
    )
    quartiers = relationship(
        "Quartier",
        backref="commune"
    )


############################
#        Table Quartier    #
############################
class Quartier(Base):
    __tablename__ = "quartiers"
    
    id = Column(
        Integer,
        primary_key=True
    )
    commune_id = Column(
        Integer,
        ForeignKey("communes.id"),
        nullable=False
    )
    quartier = Column(
        String,
        nullable=False   
    )
    
    utilisateurs = relationship(
        "Utilisateur",
        backref="quartier"
    )


##===============================================================##
##                    UTILISATEURS                               ##
##===============================================================##


##############################
#      Table Utilisateur     #
##############################

class Utilisateur(Base):
    __tablename__ = "utilisateurs"
    id = Column(Integer,primary_key=True,nullable=False)
    quartier_id = Column(Integer,ForeignKey("quartiers.id"),nullable=False)
    nom_prenom = Column(String,index=True,nullable=False)
    tel = Column(String,unique=True,nullable=False)
    genre = Column(String,nullable=False)
    email = Column(String,unique=True,nullable=False)
    mot_de_passe = Column(String,nullable=False)
    copie_pi = Column(String, nullable=False)
    role = Column(String,nullable=False)
    create_at = Column(DateTime,nullable=False)
    is_actif = Column(Boolean,nullable=False,server_default="FALSE")
    update_at = Column(DateTime,nullable=False)
    
    pmes = relationship( "Pme",backref="utilisateur")
    otp = relationship("OTP",backref="utilisateur")
    
    clients = relationship("Client",backref="utilisateur")
    abonnements = relationship("Abonnement",backref="utilisateur")
    confcalrondes = relationship( "ConfCalRonde",backref="utilisateur")
    
   
    
##############################
#        Table PME           #
##############################
class Pme(Base):
    __tablename__ = "pmes"
    
    id = Column(Integer,primary_key=True,nullable=False)
    utilisateur_id = Column(Integer,ForeignKey("utilisateurs.id"),nullable=False)
    nom_pme = Column(String,nullable=False,index=True,unique=True)
    description = Column(Text,nullable=False)
    zone_intervention = Column(String,nullable=False)
    num_enregistrement = Column(String,nullable=False,unique=True)
    tarif_mensuel = Column(Integer,nullable=False)
    tarif_abonnement = Column(Integer,nullable=False)
    logo_pme = Column(String,nullable=False)
    abonnements = relationship("Abonnement",backref="pme")
    calrondes = relationship("CalRonde",backref="pme")
   

##############################
#        Table Client        #
##############################
class Client(Base):
    __tablename__ = "clients"
    
    id = Column(
        Integer,
        primary_key=True
    )
    utilisateur_id = Column(
        Integer,
        ForeignKey("utilisateurs.id"),
        nullable=False
    )
    num_rccm = Column(
        String,
        nullable=False
    )
    nom_entreprise = Column(
        String,
        nullable=False,
        index=True
    )
   


##===============================================================##
##                    Abonnements                                ##
##===============================================================##

##############################
#      Table Abonnement      #
##############################
class Abonnement(Base):
    __tablename__ = "abonnements"
    
    id = Column(
        Integer,
        primary_key=True,
        nullable=False
    )
    utilisateurs_id = Column(
        Integer,
        ForeignKey("utilisateurs.id")
    )
    pme_id = Column(
        Integer,
        ForeignKey("pmes.id")
    )
    num_abonnement = Column(
        String,
        nullable=False
    )
    tarif_abonnement = Column(
        Integer,
        nullable=False
    )
    status_abonnement = Column(
        String,
        nullable=False
    )
    debut_abonnement = Column(
        DateTime,
        nullable=False
    )
    fin_abonnement = Column(
        DateTime,
        nullable=False
    )
   
   


##===============================================================##
##         Calendrier et confirmation des rondes                 ##
##===============================================================##

##############################
#      Table CalRonde       #
##############################

class CalRonde(Base):
    __tablename__ = "calrondes"
    
    id = Column(
        Integer,
        primary_key=True
    )
    pme_id = Column(
        Integer,
        ForeignKey("pmes.id")
    )
    jour_passage = Column(
        String,
        nullable=False
    )
    heure_passage = Column(
        String,
        nullable=False
    )
    date_creation = Column(
        DateTime,
        nullable=False
    )
    date_maj = Column(
        DateTime
    )
    
    confcalrondes = relationship(
        "ConfCalRonde",
        backref="calronde"
    )


##############################
#    Table ConfCalRonde      #
##############################  

class ConfCalRonde(Base):
    __tablename__ = "confcalrondes"
    
    id = Column(
        Integer,
        primary_key=True
    )
    calronde_id = Column(
        Integer,
        ForeignKey("calrondes.id")
    )
    utilisateur_id = Column(
        Integer,
        ForeignKey("utilisateurs.id")
    )
    conf_passage = Column(
        Boolean,
        nullable=False
    )
    date_conf_passage = Column(
        DateTime,
        nullable=False
    )
class OTP(Base):
    __tablename__ = "otps"
    id=Column(
        Integer,
        primary_key=True
    )
    otp_code= Column(
        String, 
        nullable=False
    )
    expiration_time=Column(
        DateTime,
        nullable=False
    )
    utilisateur_id = Column(
        Integer,
        ForeignKey("utilisateurs.id"),
        nullable=False
    )

class Commentaire(Base):
    __tablename__ = 'commentaire'

    id = Column(
        Integer, 
        primary_key=True,
        nullable=False
    )
    utilisateur_id = Column(
        Integer,
        ForeignKey("utilisateurs.id"),
        nullable=False
    )
    pme_id = Column(
        Integer,
        ForeignKey("pmes.id"),
        nullable=False
    )
    message = Column(
        String,
        nullable=False
    )
    note = Column(
        Integer,
        nullable=False
    )
    date_publicat = Column(
        DateTime,
        default=datetime.utcnow
    )
    auteur = Column(
        Integer,
        nullable=False
    )
