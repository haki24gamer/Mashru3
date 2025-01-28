# Mashru3

## 🌟 Description

**Mashru3** est une application web de gestion de projets conçue pour améliorer la collaboration, la planification et le suivi des tâches au sein des équipes.  
Elle offre une interface intuitive et des fonctionnalités puissantes pour permettre aux utilisateurs d'organiser leurs projets et de suivre leur progression efficacement.

---

## 🚀 Fonctionnalités principales

- **Gestion des utilisateurs :** Inscription, connexion sécurisée, rôles (administrateur, chef de projet, membre).
- **Gestion des projets :** Création, organisation et suivi des projets.
- **Gestion des tâches :** Attribution, suivi, priorisation, et affichage en Kanban et diagramme de Gantt.
- **Collaboration :** Messagerie contextuelle et notifications en temps réel.
- **Rapports et statistiques :** Génération de rapports d'avancement et de cahiers des charges.
- **Sécurisation des données :** Authentification robuste et permissions granulaires.

---

## 🛠️ Technologies utilisées

- **Backend :** [Flask](https://flask.palletsprojects.com/) (Python)
- **Base de données :** [MySQL](https://www.mysql.com/)
- **Frontend :** HTML, CSS (Bootstrap), JavaScript
- **Dépendances :** Flask-SQLAlchemy, Flask-Migrate, Flask-Login

---

## ⚙️ Installation et exécution

### Prérequis

- **Python 3.8+** installé
- **MySQL** installé et configuré
- **Git** installé

### Étapes d'installation

1. **Cloner le dépôt :**
   ```bash
   git clone [https://github.com/votre-utilisateur/mashru3](https://github.com/haki24gamer/Mashru3).git
   cd Mashru3

2. **Créer un environnement virtuel :**
   ```bash
      python -m venv venv
      source venv/bin/activate  # Pour Linux/MacOS
      venv\Scripts\activate     # Pour Windows

3. **Installer les dépendances :**
   ```bash
     pip install -r requirements.txt

4. **Configurer la base de données :**
   ```sql
     CREATE DATABASE mashru3 CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;


5. **Appliquer les migrations de la base de données :**
   ```bash
     flask db upgrade

6. **Lancer l'application :**
   ```bash
     flask run
  L'application sera accessible sur http://127.0.0.1:5000.
