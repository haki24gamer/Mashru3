📌 Tutoriel : Créer une Web App Basique avec Flask
🛠️ 1. Installation des Prérequis

Avant de commencer, assure-toi d’avoir Python installé. Ensuite, installe Flask avec :

pip install flask

📂 2. Structure du Projet

Crée un dossier pour ton projet et organise-le comme suit :

flask_app/
│── app.py
│── templates/
│   │── index.html
│── static/
│   │── style.css

🚀 3. Création du Serveur Flask

Dans app.py, écris ceci :

from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)

Explication :

    Flask(__name__) initialise l’application.
    @app.route('/') définit une route accessible à l’URL /.
    render_template('index.html') affiche une page HTML.
    app.run(debug=True) permet d’exécuter l’application en mode débogage.

🎨 4. Création de la Page HTML

Dans templates/index.html :

<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Ma Première App Flask</title>
    <link rel="stylesheet" href="{{ url_for('static', filename='style.css') }}">
</head>
<body>
    <h1>Bienvenue sur ma Web App Flask 🎉</h1>
</body>
</html>

🎨 5. Ajout d'un CSS (optionnel)

Dans static/style.css :

body {
    font-family: Arial, sans-serif;
    text-align: center;
    margin: 50px;
}
h1 {
    color: #3498db;
}

▶️ 6. Lancer l'Application

Dans le terminal, exécute :

python app.py

Ouvre ensuite ton navigateur et accède à http://127.0.0.1:5000/ 🎉
🔥 Améliorations Possibles

    Ajouter des formulaires pour interagir avec l’utilisateur.
    Connecter une base de données (SQLite/MySQL) pour stocker des données.
    Gérer des authentifications avec Flask-Login.