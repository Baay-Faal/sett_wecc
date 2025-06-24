from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime, timedelta

db = SQLAlchemy()
class User(db.Model, UserMixin):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False, unique=True)
    email = db.Column(db.String(150), nullable=False, unique=True)
    password_hash = db.Column(db.String(128), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)

    # Nouveau : ajouter ces colonnes
    nom = db.Column(db.String(100), nullable=True)
    telephone = db.Column(db.String(50), nullable=True)
    adresse = db.Column(db.String(255), nullable=True)

    # Pour suivi de statut
    status = db.Column(db.String(20), default='hors ligne')  # "en ligne" ou "hors ligne"
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)

    commandes = db.relationship("Commande", backref="client", lazy=True)

    def __repr__(self):
        return f'<User {self.username} | {"Admin" if self.is_admin else "Client"}>'

    def set_online(self):
        self.status = "en ligne"
        self.last_seen = datetime.utcnow()

    def set_offline(self):
        self.status = "hors ligne"


class Admin(db.Model, UserMixin):
    __tablename__ = 'admin'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)


class Commande(db.Model):
    __tablename__ = 'commande'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    nom = db.Column(db.String(100), nullable=False)
    adresse = db.Column(db.String(255), nullable=False)
    telephone = db.Column(db.String(50), nullable=False)

    forfait = db.Column(db.String(50), nullable=False)  # simple, semi_premium, premium
    date_commande = db.Column(db.DateTime, default=datetime.utcnow)
    date_retrait = db.Column(db.DateTime)
    date_livraison = db.Column(db.DateTime)

    prix_total = db.Column(db.Integer, nullable=False, default=0)

    moyen_paiement = db.Column(db.String(50), nullable=True)  # ex: 'wave', 'orange money', 'wixx by yas'

    quantites = db.Column(db.Text, nullable=True)

    articles = db.relationship('ArticleCommande', backref='commande', lazy=True, cascade="all, delete-orphan")

    def calculer_dates(self):
        self.date_retrait = self.date_commande + timedelta(days=1)
        if self.forfait == 'premium':
            self.date_livraison = self.date_retrait + timedelta(days=1)
        elif self.forfait == 'semi_premium':
            self.date_livraison = self.date_retrait + timedelta(days=2)
        else:  # simple
            self.date_livraison = self.date_retrait + timedelta(days=3)



class ArticleCommande(db.Model):
    __tablename__ = 'article_commande'

    id = db.Column(db.Integer, primary_key=True)
    commande_id = db.Column(db.Integer, db.ForeignKey('commande.id'), nullable=False)
    nom_article = db.Column(db.String(100), nullable=False)
    quantite = db.Column(db.Integer, nullable=False)
    prix_unitaire = db.Column(db.Integer, nullable=False)
    remise = db.Column(db.Integer, default=0)
    total_article = db.Column(db.Integer, nullable=False)
