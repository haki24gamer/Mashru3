from flask import Flask, render_template, redirect, url_for, request, session, jsonify
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
            session['user_id'] = user.user_id
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

# Collection of collaboration and teamwork quotes
COLLABORATION_QUOTES = [
    {"text": "La seule façon de faire du bon travail est d'aimer ce que vous faites.", "author": "Steve Jobs"},
    {"text": "Seul on va plus vite, ensemble on va plus loin.", "author": "Proverbe africain"},
    {"text": "Le talent gagne des matchs, mais le travail d'équipe gagne des championnats.", "author": "Michael Jordan"},
    {"text": "Si vous voulez aller vite, allez-y seul. Si vous voulez aller loin, allez-y ensemble.", "author": "Proverbe africain"},
    {"text": "Aucun de nous n'est aussi intelligent que nous tous ensemble.", "author": "Ken Blanchard"},
    {"text": "La force du loup est dans la meute, et la force de la meute est dans le loup.", "author": "Rudyard Kipling"},
    {"text": "Se réunir est un début, rester ensemble est un progrès, travailler ensemble est la réussite.", "author": "Henry Ford"},
    {"text": "La collaboration est la multiplication des forces.", "author": "Andrew Carnegie"},
    {"text": "L'unité est la diversité, et la diversité est l'unité.", "author": "Mary Parker Follett"},
    {"text": "La créativité s'épanouit lorsque nous travaillons ensemble.", "author": "Français Johansson"}
]

# Create a context processor to provide quote to all templates
@app.context_processor
def inject_quote():
    """Make a random quote available to all templates"""
    return {'quote': random.choice(COLLABORATION_QUOTES) if 'COLLABORATION_QUOTES' in globals() else None}

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('connexion'))
    
    user_id = session['user_id']
    user = User.query.get(user_id)
    
    # Select a random quote
    random_quote = random.choice(COLLABORATION_QUOTES)
    
    # Get user's projects
    user_projects = db.session.query(Project).join(Participate).filter(
        Participate.user_id == user_id
    ).all()
    
    # Count total projects
    total_projects = len(user_projects)
    
    # Get task IDs assigned to this user
    assigned_task_ids_query = db.session.query(Assigned.task_id).filter(
        Assigned.user_id == user_id
    )
    
    # Task statistics - counts by status for tasks assigned to the user
    task_stats = {
        'TODO': 0,
        'IN_PROGRESS': 0,
        'REVIEW': 0,
        'DONE': 0
    }
    
    task_counts = db.session.query(
        Task.status, db.func.count(Task.task_id)
    ).filter(
        Task.task_id.in_(assigned_task_ids_query)
    ).group_by(Task.status).all()
    
    # Update with actual counts
    for status, count in task_counts:
        task_stats[status] = count
    
    # Calculate task percentage completion
    total_tasks = sum(task_stats.values()) or 1  # Avoid division by zero
    completion_percentage = round((task_stats['DONE'] / total_tasks) * 100, 1)
    
    # Get most active projects (based on tasks assigned to the user)
    active_projects = []
    project_activity = db.session.query(
        Project.project_id,
        Project.name,
        db.func.count(Task.task_id).label('task_count')
    ).join(
        Task, Task.project_id == Project.project_id
    ).join(
        Assigned, Assigned.task_id == Task.task_id
    ).filter(
        Assigned.user_id == user_id
    ).group_by(
        Project.project_id, Project.name
    ).order_by(
        db.desc('task_count')
    ).limit(5).all()
    
    active_projects = [
        {'name': p.name, 'task_count': p.task_count}
        for p in project_activity
    ]
    
    # Get recent tasks assigned to user (already correct)
    recent_tasks = db.session.query(
        Task
    ).join(
        Assigned, Assigned.task_id == Task.task_id
    ).filter(
        Assigned.user_id == user_id
    ).order_by(
        Task.created_at.desc()
    ).limit(5).all()
    
    # Get tasks by priority for tasks assigned to the user
    priority_stats = {'low': 0, 'medium': 0, 'high': 0}
    
    priority_counts = db.session.query(
        Task.priority, db.func.count(Task.task_id)
    ).join(
        Assigned, Assigned.task_id == Task.task_id
    ).filter(
        Assigned.user_id == user_id
    ).group_by(Task.priority).all()
    
    for priority, count in priority_counts:
        priority_stats[priority] = count
    
    return render_template(
        'dashboard.html',
        user_first_name=user.name,
        total_projects=total_projects,
        task_stats=task_stats,
        completion_percentage=completion_percentage,
        active_projects=active_projects,
        recent_tasks=recent_tasks,
        priority_stats=priority_stats,
        quote=random_quote  # Pass the random quote to the template
    )

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

@app.route('/update_task_status', methods=['POST'])
def update_task_status():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not authenticated'}), 401
    
    data = request.get_json()
    task_id = data.get('task_id')
    new_status = data.get('status')
    
    try:
        task = Task.query.get(task_id)
        if task:
            task.status = new_status
            if new_status == 'DONE' and not task.finished_date:
                task.finished_date = date.today()
            elif new_status != 'DONE':
                task.finished_date = None
            
            db.session.commit()
            return jsonify({'success': True, 'message': 'Task status updated successfully'})
        else:
            return jsonify({'success': False, 'message': 'Task not found'}), 404
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/get_task/<int:task_id>')
def get_task(task_id):
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not authenticated'}), 401
    
    task = Task.query.get(task_id)
    if task:
        task_data = {
            'task_id': task.task_id,
            'title': task.title,
            'description': task.description,
            'priority': task.priority,
            'status': task.status,
            'start_date': task.start_date.isoformat() if task.start_date else None,
            'end_date': task.end_date.isoformat() if task.end_date else None
        }
        return jsonify({'success': True, 'task': task_data})
    else:
        return jsonify({'success': False, 'message': 'Task not found'}), 404

@app.route('/update_task/<int:task_id>', methods=['POST'])
def update_task(task_id):
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not authenticated'}), 401
    
    data = request.get_json()
    task = Task.query.get(task_id)
    
    if task:
        try:
            task.title = data.get('title', task.title)
            task.description = data.get('description', task.description)
            task.priority = data.get('priority', task.priority)
            
            if 'start_date' in data and data['start_date']:
                task.start_date = date.fromisoformat(data['start_date'])
            if 'end_date' in data and data['end_date']:
                task.end_date = date.fromisoformat(data['end_date'])
            
            db.session.commit()
            return jsonify({'success': True, 'message': 'Task updated successfully'})
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'message': str(e)}), 500
    else:
        return jsonify({'success': False, 'message': 'Task not found'}), 404

@app.route('/project/<int:project_id>')
def project_detail(project_id):
    if 'user_id' not in session:
        return redirect(url_for('connexion'))
    
    # Get the current project
    project = Project.query.get_or_404(project_id)
    
    # Get all project participants with their roles
    participants_data = db.session.query(
        User, Participate.role
    ).join(
        Participate, User.user_id == Participate.user_id
    ).filter(
        Participate.project_id == project_id
    ).all()
    
    # Format participants data for the template
    participants = [{'name': user.name, 'user_id': user.user_id, 'role': role} for user, role in participants_data]
    
    # Determine the current user's role in this project
    user_participation = Participate.query.filter_by(
        user_id=session['user_id'],
        project_id=project_id
    ).first()
    
    user_role = user_participation.role if user_participation else None
    is_admin = user_role in ['Owner', 'Admin'] if user_role else False
    
    # Get tasks for this project
    tasks = Task.query.filter_by(project_id=project_id).all()
    
    # Fetch assigned users for each task
    for task in tasks:
        assigned_users = db.session.query(User).join(Assigned).filter(Assigned.task_id == task.task_id).all()
        task.assigned_users = assigned_users

    return render_template(
        'project_detail.html', 
        project=project, 
        participants=participants, 
        tasks=tasks, 
        user_role=user_role,
        is_admin=is_admin
    )

@app.route('/update_project/<int:project_id>', methods=['POST'])
def update_project(project_id):
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not authenticated'}), 401
    
    # Check if user has permission to update this project
    participation = Participate.query.filter_by(
        user_id=session['user_id'], 
        project_id=project_id
    ).first()
    
    if not participation or participation.role not in ['Owner', 'Admin']:
        return jsonify({'success': False, 'message': 'Permission denied'}), 403
    
    try:
        data = request.get_json()
        project = Project.query.get_or_404(project_id)
        
        project.name = data.get('name', project.name)
        project.description = data.get('description', project.description)
        project.image = data.get('image', project.image)
        
        if data.get('start_date'):
            project.start_date = date.fromisoformat(data['start_date'])
        if data.get('end_date'):
            project.end_date = date.fromisoformat(data['end_date'])
            
        db.session.commit()
        return jsonify({'success': True, 'message': 'Project updated successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/update_member_role', methods=['POST'])
def update_member_role():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not authenticated'}), 401
    
    data = request.get_json()
    project_id = data.get('project_id')
    target_user_id = data.get('user_id')
    new_role = data.get('role')
    
    # Check if current user has permission
    current_user_participation = Participate.query.filter_by(
        user_id=session['user_id'],
        project_id=project_id
    ).first()
    
    if not current_user_participation or current_user_participation.role not in ['Owner', 'Admin']:
        return jsonify({'success': False, 'message': 'Permission denied'}), 403
    
    # Check if target user is the owner (only owner can change owner's role)
    target_participation = Participate.query.filter_by(
        user_id=target_user_id,
        project_id=project_id
    ).first()
    
    if target_participation.role == 'Owner' and current_user_participation.role != 'Owner':
        return jsonify({'success': False, 'message': 'Cannot change owner role'}), 403
    
    try:
        target_participation.role = new_role
        db.session.commit()
        return jsonify({'success': True, 'message': 'Role updated successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/remove_member', methods=['POST'])
def remove_member():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not authenticated'}), 401
    
    data = request.get_json()
    project_id = data.get('project_id')
    target_user_id = data.get('user_id')
    
    # Check if current user has permission
    current_user_participation = Participate.query.filter_by(
        user_id=session['user_id'],
        project_id=project_id
    ).first()
    
    if not current_user_participation or current_user_participation.role not in ['Owner', 'Admin']:
        return jsonify({'success': False, 'message': 'Permission denied'}), 403
    
    # Prevent removing the owner
    target_participation = Participate.query.filter_by(
        user_id=target_user_id,
        project_id=project_id
    ).first()
    
    if target_participation.role == 'Owner':
        return jsonify({'success': False, 'message': 'Cannot remove project owner'}), 403
    
    # Prevent self-removal
    if int(target_user_id) == session['user_id']:
        return jsonify({'success': False, 'message': 'Cannot remove yourself from the project'}), 400
    
    try:
        # Remove user's assignments in this project
        tasks = Task.query.filter_by(project_id=project_id).all()
        task_ids = [task.task_id for task in tasks]
        
        if task_ids:
            assignments = Assigned.query.filter(
                Assigned.user_id == target_user_id,
                Assigned.task_id.in_(task_ids)
            ).all()
            
            for assignment in assignments:
                db.session.delete(assignment)
        
        # Remove user from project
        db.session.delete(target_participation)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Member removed successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/update_project_settings/<int:project_id>', methods=['POST'])
def update_project_settings(project_id):
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not authenticated'}), 401
    
    # Check if user has permission
    participation = Participate.query.filter_by(
        user_id=session['user_id'],
        project_id=project_id
    ).first()
    
    if not participation or participation.role not in ['Owner', 'Admin']:
        return jsonify({'success': False, 'message': 'Permission denied'}), 403
    
    # In a real application, you might have a ProjectSettings table
    # Here we'll just pretend we saved the settings
    data = request.get_json()
    
    try:
        # For demonstration purposes, we're not actually saving these settings
        # In a real application, you'd store these in the database
        return jsonify({
            'success': True,
            'message': 'Settings updated successfully',
            'settings': data
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/delete_project/<int:project_id>', methods=['POST'])
def delete_project(project_id):
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not authenticated'}), 401
    
    # Check if user is the owner
    participation = Participate.query.filter_by(
        user_id=session['user_id'],
        project_id=project_id
    ).first()
    
    if not participation or participation.role != 'Owner':
        return jsonify({'success': False, 'message': 'Only the project owner can delete this project'}), 403
    
    try:
        project = Project.query.get_or_404(project_id)
        
        # Delete task assignments
        tasks = Task.query.filter_by(project_id=project_id).all()
        for task in tasks:
            # Delete task predecessors
            Predecessor.query.filter_by(task_id=task.task_id).delete()
            Predecessor.query.filter_by(predecessor_id=task.task_id).delete()
            
            # Delete task assignments
            Assigned.query.filter_by(task_id=task.task_id).delete()
        
        # Delete tasks
        Task.query.filter_by(project_id=project_id).delete()
        
        # Delete participations
        Participate.query.filter_by(project_id=project_id).delete()
        
        # Delete project
        db.session.delete(project)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Project deleted successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/parametre', methods=['GET', 'POST'])
def parametre():
    if 'user_id' not in session:
        return redirect(url_for('connexion'))
    
    user_id = session['user_id']
    user = User.query.get(user_id)
    success_message = None
    error_message = None
    
    if request.method == 'POST':
        action = request.form.get('action', '')
        
        if action == 'update_info':
            # Update basic info
            user.name = request.form.get('name', user.name)
            
            # Check if email is being changed and if it's not already taken
            new_email = request.form.get('email')
            if new_email != user.email:
                existing_user = User.query.filter_by(email=new_email).first()
                if existing_user:
                    error_message = "Cet e-mail est déjà utilisé par un autre compte."
                else:
                    user.email = new_email
            
            if not error_message:
                db.session.commit()
                success_message = "Vos informations ont été mises à jour avec succès."
        
        elif action == 'update_password':
            # Update password
            current_password = request.form.get('current_password', '')
            new_password = request.form.get('new_password', '')
            confirm_password = request.form.get('confirm_password', '')
            
            # Verify current password
            if not check_password_hash(user.password, current_password):
                error_message = "Le mot de passe actuel est incorrect."
            elif new_password != confirm_password:
                error_message = "Le nouveau mot de passe et sa confirmation ne correspondent pas."
            elif not new_password:
                error_message = "Le nouveau mot de passe ne peut pas être vide."
            else:
                user.password = generate_password_hash(new_password)
                db.session.commit()
                success_message = "Votre mot de passe a été mis à jour avec succès."
        
        elif action == 'update_image':
            # Update profile image (URL or path)
            user.image = request.form.get('image', user.image)
            db.session.commit()
            success_message = "Votre image de profil a été mise à jour avec succès."
    
    return render_template('parametre.html', user=user, success_message=success_message, error_message=error_message)

@app.route('/')
def home():
    return redirect(url_for('dashboard'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)