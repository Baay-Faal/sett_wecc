from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from models import db, User
from models import Admin
from models import Commande
from models import ArticleCommande
from flask import make_response
from flask import session, flash, redirect, render_template, request, url_for
from flask_mail import Mail, Message
import json


app = Flask(__name__)
app.secret_key = 'votre_clef_secrete'  # Change ça

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///sett_wecc.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'connexion'

app.config.update(
    MAIL_SERVER='smtp.gmail.com',
    MAIL_PORT=587,
    MAIL_USE_TLS=True,
    MAIL_USERNAME='ton.email@gmail.com',       # Remplace par ton email
    MAIL_PASSWORD='ton_mot_de_passe_app',       # Mot de passe ou mot de passe d’application Gmail
)

mail = Mail(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.before_request
def update_user_status():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
        current_user.status = "en ligne"
        db.session.commit()

@app.route('/')
def accueil():
    return render_template('index.html')

@app.route('/services')
@login_required
def services():
    return render_template('services.html')

@app.route('/panier')
@login_required
def panier():
    panier = session.get('panier', None)
    if not panier:
        flash("Aucun service sélectionné pour le moment.", "warning")
        return redirect(url_for('services'))

    # Calcul du total pour affichage côté serveur (optionnel)
    total = 0
    PRIX_UNITAIRE = {
        'chemises': 500,
        '3_pieces': 2500,
        'baay_lahad': 1500,
        'souhaibou': 1500,
        'obasanjo': 1000,
        'draps': 1000
    }
    forfait_prix = {'simple': 0, 'semi_premium': 2500, 'premium': 5000}

    articles = panier['articles']
    for art, qte in articles.items():
        prix = PRIX_UNITAIRE.get(art, 0)
        # Ici tu peux reprendre la logique de remise selon les articles
        if art == 'chemises':
            if qte < 3:
                qte = 3
            total += prix * qte
        elif art == '3_pieces':
            remise = 250 * qte if qte > 3 else 0
            total += (prix * qte) - remise
        elif art in ['baay_lahad', 'souhaibou']:
            remise = 150 * qte if qte > 3 else 0
            total += (prix * qte) - remise
        elif art == 'obasanjo':
            remise = 100 * qte if qte > 3 else 0
            total += (prix * qte) - remise
        else:
            total += prix * qte

    total += forfait_prix.get(panier['forfait'], 0)

    return render_template('panier.html', panier=panier, total=total)


@app.route('/blog')
def blog():
    return render_template('blog.html')

@app.route('/a_propos')
def a_propos():
    return render_template('a_propos.html')


@app.route('/inscription', methods=['GET', 'POST'])
def inscription():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = generate_password_hash(request.form['password'])

        if User.query.filter_by(email=email).first():
            flash("Email déjà utilisé", "danger")
            return redirect(url_for('inscription'))

        new_user = User(username=username, email=email, password_hash=password, is_admin=False)
        db.session.add(new_user)
        db.session.commit()
        flash("Inscription réussie, connectez-vous.", "success")
        return redirect(url_for('connexion'))

    return render_template('inscription.html')

@app.route('/connexion', methods=['GET', 'POST'])
def connexion():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if not username or not password:
            flash("Veuillez remplir tous les champs.", "warning")
            return render_template('connexion.html')

        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            user.status = "en ligne"
            db.session.commit()
            # On met un flag session pour indiquer la réussite
            session['connexion_reussie'] = True
            return redirect(url_for('success'))
        else:
            flash("Échec de connexion, veuillez vérifier vos identifiants.", "danger")
            return render_template('connexion.html')

    return render_template('connexion.html')

@app.route('/success')
@login_required
def success():
    if session.get('connexion_reussie'):
        session.pop('connexion_reussie', None)  # on nettoie le flag
        return render_template('success.html')
    else:
        return redirect(url_for('connexion'))

@app.route('/deconnexion')
@login_required
def deconnexion():
    current_user.status = "hors ligne"
    db.session.commit()
    logout_user()
    flash("Déconnecté avec succès.", "info")
    return redirect(url_for('connexion'))  # redirection vers page de connexion

@app.after_request
def add_header(response):
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response


@app.route('/dashboard')
@login_required
def dashboard():
    if current_user.is_admin:
        return redirect(url_for('dashboard'))
    return render_template('dashboard.html', user=current_user)



@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        admin = Admin.query.filter_by(email=email).first()
        if admin and check_password_hash(admin.password_hash, password):
            session['admin_authenticated'] = True  # connecté avec email/mdp OK
            return redirect(url_for('admin_2fa'))
        else:
            flash("Email ou mot de passe incorrect.", "danger")
    return render_template('admin_login.html')

@app.route('/admin_2fa', methods=['GET', 'POST'])
def admin_2fa():
    if 'admin_authenticated' not in session:
        return redirect(url_for('admin_login'))

    error = None

    if request.method == 'POST':
        code_saisi = ''.join([request.form.get(f'code{i}') for i in range(1,7)])
        code_attendu = '123456'

        if code_saisi == code_attendu:
            session['admin_verified'] = True
            # Redirige vers dashboard avec paramètre success=1
            return redirect(url_for('admin_dashboard', success=1))
        else:
            error = "Code incorrect. Veuillez réessayer."

    return render_template('admin_2fa.html', error=error)


@app.route('/admin/register', methods=['GET', 'POST'])
def admin_register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')

        if not username or not email or not password:
            flash("Veuillez remplir tous les champs.", "warning")
            return render_template('admin_register.html')

        # Vérifie si email existe déjà
        existing_admin = Admin.query.filter_by(email=email).first()
        if existing_admin:
            flash("Un compte avec cet email existe déjà.", "danger")
            return render_template('admin_register.html')

        # Crée un nouvel admin avec mot de passe hashé
        new_admin = Admin(
            username=username,
            email=email,
            password_hash=generate_password_hash(password)
        )
        db.session.add(new_admin)
        db.session.commit()

        flash("Compte administrateur créé avec succès ! Vous pouvez maintenant vous connecter.", "success")
        return redirect(url_for('admin_login'))

    return render_template('admin_register.html')

@app.route('/admin/dashboard')
def admin_dashboard():
    if not session.get('admin_authenticated') or not session.get('admin_verified'):
        flash("Veuillez entrer le code pour accéder au tableau de bord.", "warning")
        return redirect(url_for('admin_login'))

    admins = Admin.query.all()
    users = User.query.filter_by(is_admin=False).all()  # Tous les utilisateurs non admin
    return render_template('admin.html', admins=admins, users=users)



@app.route('/admin/logout')
def admin_logout():
    session.clear()
    flash("Déconnexion réussie.", "success")
    return redirect(url_for('admin_login'))

from flask import session

@app.route('/valider_commande', methods=['POST'])
@login_required
def valider_commande():
    articles = request.form.getlist('articles')
    types_services = request.form.getlist('type_service')
    forfait = request.form.get('forfait')
    quantites = {}

    for article in articles:
        quantite = request.form.get(f"quantite_{article}")
        if quantite:
            quantites[article] = int(quantite)

    # Enregistrer dans session
    session['panier'] = {
        'articles': quantites,
        'services': types_services,
        'forfait': forfait
    }

    return redirect(url_for('panier'))
from datetime import datetime, timedelta
from flask import request, redirect, url_for, flash
from flask_login import login_required, current_user


@app.route('/confirmer_commande', methods=['POST'])
@login_required
def confirmer_commande():
    nom = request.form.get('nom')
    telephone = request.form.get('telephone')
    adresse = request.form.get('adresse')
    commentaires = request.form.get('commentaires')
    forfait = request.form.get('forfait')

    quantites = {}
    for key, value in request.form.items():
        if key.startswith('quantite_'):
            article = key.replace('quantite_', '')
            try:
                qte = int(value)
            except ValueError:
                qte = 0
            if qte > 0:
                quantites[article] = qte

    if not quantites:
        flash("Aucun article sélectionné.", "danger")
        return redirect(url_for('panier'))

    now = datetime.utcnow()
    date_retrait = now + timedelta(hours=24)
    if forfait == 'premium':
        date_livraison = date_retrait + timedelta(days=1)
    elif forfait == 'semi_premium':
        date_livraison = date_retrait + timedelta(days=2)
    else:
        date_livraison = date_retrait + timedelta(days=3)

    PRIX_UNITAIRE = {
        'chemises': 500,
        '3_pieces': 2500,
        'baay_lahad': 1500,
        'souhaibou': 1500,
        'obasanjo': 1000,
        'draps': 1000
    }
    forfait_prix = {'simple': 0, 'semi_premium': 2500, 'premium': 5000}

    prix_total = forfait_prix.get(forfait, 0)

    nouvelle_commande = Commande(
        user_id=current_user.id,
        nom=nom,
        telephone=telephone,
        adresse=adresse,
        forfait=forfait,
        date_commande=now,
        date_retrait=date_retrait,
        date_livraison=date_livraison,
        prix_total=0  # on mettra à jour après calcul
    )
    db.session.add(nouvelle_commande)
    db.session.flush()  # pour récupérer l'ID avant commit

    for art, qte in quantites.items():
        prix_unitaire = PRIX_UNITAIRE.get(art, 0)
        remise = 0
        # Appliquer la remise selon tes règles (exemple)
        if art == 'chemises' and qte < 3:
            qte = 3  # minimum 3 chemises
        if art == '3_pieces' and qte > 3:
            remise = 250 * qte
        if art in ['baay_lahad', 'souhaibou'] and qte > 3:
            remise = 150 * qte
        if art == 'obasanjo' and qte > 3:
            remise = 100 * qte

        total_article = prix_unitaire * qte - remise
        prix_total += total_article

        article_commande = ArticleCommande(
            commande_id=nouvelle_commande.id,
            nom_article=art,
            quantite=qte,
            prix_unitaire=prix_unitaire,
            remise=remise,
            total_article=total_article
        )
        db.session.add(article_commande)

    # Ajout prix forfait
    prix_total += forfait_prix.get(forfait, 0)
    nouvelle_commande.prix_total = prix_total

    db.session.commit()

    flash("Service confirmé. Notre camion passera dans les 24h.", "success")

    session['commande_en_attente_id'] = nouvelle_commande.id
    return redirect(url_for('facture'))


@app.route('/facture')
@login_required
def facture():
    commande_id = session.get('commande_en_attente_id')
    if not commande_id:
        flash("Aucune commande trouvée.", "danger")
        return redirect(url_for('dashboard'))

    commande = Commande.query.get_or_404(commande_id)

    # Si commande.articles est stocké en string JSON, le parser :
    try:
        articles = json.loads(commande.articles)
    except Exception:
        articles = {}

    return render_template('facture.html', commande=commande, articles=articles)




@app.route('/payer_commande', methods=['POST'])
@login_required
def payer_commande():
    commande_id = request.form.get('commande_id')
    moyen_paiement = request.form.get('moyen_paiement')

    if not commande_id or not moyen_paiement:
        flash("Données de paiement manquantes.", "danger")
        return redirect(url_for('dashboard'))

    commande = Commande.query.get_or_404(commande_id)

    if commande.user_id != current_user.id:
        flash("Accès non autorisé à cette commande.", "danger")
        return redirect(url_for('dashboard'))

    # Mise à jour de la commande
    commande.statut = "payée"
    commande.moyen_paiement = moyen_paiement
    db.session.commit()

    # Récupérer les articles liés à cette commande
    articles = ArticleCommande.query.filter_by(commande_id=commande.id).all()

    # Préparer et envoyer l'e-mail
    msg = Message(
        subject=f"Facture commande #{commande.id} - SETT WECC",
        sender=app.config['MAIL_USERNAME'],
        recipients=[current_user.email]
    )

    msg.html = render_template('email_facture.html',
                               commande=commande,
                               articles=articles,
                               utilisateur=current_user,
                               moyen_paiement=moyen_paiement)

    try:
        mail.send(msg)
        flash("Paiement validé. Un email de confirmation vous a été envoyé.", "success")
    except Exception as e:
        flash("Paiement validé mais l'envoi de l'email a échoué.", "warning")
        print("Erreur d'envoi d'email :", e)

    return redirect(url_for('dashboard'))


@app.template_filter('currency_xof')
def currency_xof_filter(value):
    try:
        value = int(value)
        # Formattage simple avec séparateur de milliers
        return f"{value:,} XOF".replace(",", " ")
    except Exception:
        return value


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
