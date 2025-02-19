from flask import Flask, render_template, redirect, url_for, request, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import date
import mysql.connector
from email.message import EmailMessage
from flask_mail import Mail, Message
import random

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:@localhost/Mashru3'
app.config['SECRET_KEY'] = 'your_secret_key'
db = SQLAlchemy(app)

# Configure Flask-Mail for Gmail
app.config['MAIL_SERVER'] = 'smtp.gmail.com'  # Gmail SMTP server
app.config['MAIL_PORT'] = 587  # Port for TLS
app.config['MAIL_USERNAME'] = 'mashru3.djib@gmail.com'  # Replace with your Gmail address
app.config['MAIL_PASSWORD'] = 'csmk klck zzxm oldg '  # Replace with your app password (not your Gmail password)
app.config['MAIL_USE_TLS'] = True  # Use TLS
app.config['MAIL_USE_SSL'] = False  # Don't use SSL
mail = Mail(app)

# Function to create database if it doesn't exist
def create_database():
    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password=""
    )
    cursor = conn.cursor()
    cursor.execute("CREATE DATABASE IF NOT EXISTS Mashru3")
    conn.close()


# User table
class User(db.Model):
    user_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    image = db.Column(db.String(255))
    password = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)

# Project table
class Project(db.Model):
    project_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    image = db.Column(db.String(255))
    start_date = db.Column(db.DATE, nullable=True)
    end_date = db.Column(db.DATE, nullable=True)
    finished_date = db.Column(db.DATE, nullable=True)
    created_at = db.Column(db.DATE, server_default=db.func.current_date())

# Participate table
class Participate(db.Model):
    user_id = db.Column(db.Integer, db.ForeignKey('user.user_id'), primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('project.project_id'), primary_key=True)
    role = db.Column(db.String(50), nullable=False)
    created_at = db.Column(db.DATE, server_default=db.func.current_date())

# Task table
class Task(db.Model):
    task_id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('project.project_id'), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    priority = db.Column(db.Enum('low', 'medium', 'high'), nullable=False)
    status = db.Column(db.Enum('TODO', 'IN_PROGRESS', 'REVIEW', 'DONE'), default='TODO')
    start_date = db.Column(db.DATE, nullable=True)
    end_date = db.Column(db.DATE, nullable=True)
    finished_date = db.Column(db.DATE, nullable=True)
    created_at = db.Column(db.DATE, server_default=db.func.current_date())

# Predecessor table
class Predecessor(db.Model):
    task_id = db.Column(db.Integer, db.ForeignKey('task.task_id'), primary_key=True)
    predecessor_id = db.Column(db.Integer, db.ForeignKey('task.task_id'), primary_key=True)
    created_at = db.Column(db.DATE, server_default=db.func.current_date())

# Assigned table
class Assigned(db.Model):
    user_id = db.Column(db.Integer, db.ForeignKey('user.user_id'), primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey('task.task_id'), primary_key=True)
    note = db.Column(db.Text)
    created_at = db.Column(db.DATE, server_default=db.func.current_date())

# Ensure the database and tables are created
with app.app_context():
    create_database()  # Ensure database exists
    db.create_all()    # Create tables if they don't exist

@app.route('/connexion', methods=['GET', 'POST'])
def connexion():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.user_id  # Session starts here
            return redirect(url_for('dashboard'))
        else:
            return "Invalid credentials"
    return render_template('connexion.html')

@app.route('/inscription', methods=['GET', 'POST'])
def inscription():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = generate_password_hash(request.form['password'])
        
        # Generate OTP and store registration data in session
        otp = str(random.randint(100000, 999999))
        session['registration_data'] = {'name': name, 'email': email, 'password': password}
        session['otp'] = otp
        
        # Send OTP to user's email
        msg = Message('OTP Verification', sender=app.config['MAIL_USERNAME'], recipients=[email])
        msg.body = f'Your OTP is: {otp}'
        mail.send(msg)
        
        return redirect(url_for('verify_otp'))
    return render_template('inscription.html')

@app.route('/verify_otp', methods=['GET', 'POST'])
def verify_otp():
    # Redirect if no registration data present
    if 'registration_data' not in session or 'otp' not in session:
        return redirect(url_for('inscription'))
    error = None
    if request.method == 'POST':
        if request.form['otp'] == session['otp']:
            data = session['registration_data']
            # Create the user in the database
            new_user = User(name=data['name'], email=data['email'], password=data['password'])
            db.session.add(new_user)
            db.session.commit()
            # Clear registration data from session
            session.pop('registration_data', None)
            session.pop('otp', None)
            return redirect(url_for('connexion'))
        else:
            error = 'Invalid OTP'
    return render_template('verify_otp.html', error=error)

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('connexion'))
    user = User.query.get(session['user_id'])
    return render_template('dashboard.html', user_first_name=user.name)

@app.route('/projects')
def projects():
    if 'user_id' not in session:
        return redirect(url_for('connexion'))
    user_id = session['user_id']
    user_projects = db.session.query(Project).join(Participate).filter(Participate.user_id == user_id).all()
    total_projects = len(user_projects)
    return render_template('project.html', projects=user_projects, total_projects=total_projects)

@app.route('/add_project', methods=['GET', 'POST'])
def add_project():
    if 'user_id' not in session:
        return redirect(url_for('connexion'))
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        image = request.form['image']
        start_date = request.form['start_date']
        end_date = request.form['end_date']
        created_at = date.today()
        new_project = Project(name=name, description=description, image=image, start_date=start_date, end_date=end_date, created_at=created_at)
        db.session.add(new_project)
        db.session.commit()
        user_id = session['user_id']
        new_participate = Participate(role='Owner', user_id=user_id, project_id=new_project.project_id)
        db.session.add(new_participate)
        db.session.commit()
        return redirect(url_for('projects'))
    return render_template('add_project.html')

@app.route('/add_task', methods=['POST'])
def add_task():
    if 'user_id' not in session:
        return redirect(url_for('connexion'))
    data = request.get_json()
    new_task = Task(
        project_id=data['project_id'],
        title=data['title'],
        description=data['description'],
        priority=data['priority'],
        status=data['status'],
        start_date=data['start_date'],
        end_date=data['end_date']
    )
    db.session.add(new_task)
    db.session.commit()

    return {'message': 'Task created successfully'}, 200

@app.route('/add_member', methods=['POST'])
def add_member():
    if 'user_id' not in session:
        return redirect(url_for('connexion'))
    data = request.get_json()
    user = User.query.filter_by(email=data['email']).first()
    if user:
        new_participate = Participate(
            user_id=user.user_id,
            project_id=data['project_id'],
            role=data['role']
        )
        db.session.add(new_participate)
        db.session.commit()
        return {'message': 'Member added successfully'}, 200
    else:
        return {'message': 'User not found'}, 404

@app.route('/assign_user', methods=['POST'])
def assign_user():
    if 'user_id' not in session:
        return redirect(url_for('connexion'))
    data = request.get_json()
    user_ids = data['user_ids']
    task_id = data['task_id']
    note = data.get('note', '')

    for user_id in user_ids:
        # Check if the user is already assigned to the task
        existing_assignment = Assigned.query.filter_by(user_id=user_id, task_id=task_id).first()
        if not existing_assignment:
            new_assignment = Assigned(user_id=user_id, task_id=task_id, note=note)
            db.session.add(new_assignment)

    db.session.commit()
    return {'message': 'User(s) assigned successfully'}, 200

@app.route('/project/<int:project_id>')
def project_detail(project_id):
    if 'user_id' not in session:
        return redirect(url_for('connexion'))
    project = Project.query.get_or_404(project_id)
    participants = db.session.query(User).join(Participate).filter(Participate.project_id == project_id).all()
    tasks = Task.query.filter_by(project_id=project_id).all()
    
    # Fetch assigned users for each task
    for task in tasks:
        assigned_users = db.session.query(User).join(Assigned).filter(Assigned.task_id == task.task_id).all()
        task.assigned_users = assigned_users

    return render_template('project_detail.html', project=project, participants=participants, tasks=tasks)

@app.route('/logout')
def logout():
    session.clear()  # Session ends here
    return redirect(url_for('connexion'))

@app.route('/')
def home():
    return redirect(url_for('dashboard'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)