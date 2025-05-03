from flask import Flask, render_template, redirect, url_for, request, session, jsonify, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import date
from email.message import EmailMessage
from flask_mail import Mail, Message as MailMessage
import random
import os
from datetime import datetime, timedelta
import time
try:
    import mysql.connector
except ImportError:
    # MySQL connector not installed
    mysql = None
import openai
from dotenv import load_dotenv
load_dotenv()

# Configure OpenAI API key from environment
openai.api_key = os.getenv('OPENAI_API_KEY')  # Ensure OPENAI_API_KEY is set via .env or environment

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///project.db'
app.config['SECRET_KEY'] = 'your_secret_key'
db = SQLAlchemy(app)

# Configure Flask-Mail for Gmail
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USERNAME'] = 'mashru3.djib@gmail.com'
app.config['MAIL_PASSWORD'] = 'csmk klck zzxm oldg '
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False
mail = Mail(app)

# Configure uploads directories
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'uploads')
app.config['PROFILE_PICS_FOLDER'] = os.path.join(app.config['UPLOAD_FOLDER'], 'profile_pics')
app.config['PROJECT_IMAGES_FOLDER'] = os.path.join(app.config['UPLOAD_FOLDER'], 'project_images')
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # 5MB max upload

# Make sure upload directories exist
os.makedirs(app.config['PROFILE_PICS_FOLDER'], exist_ok=True)
os.makedirs(app.config['PROJECT_IMAGES_FOLDER'], exist_ok=True)

# Helper function to check allowed file extensions
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

# Serve favicon from static folder
@app.route('/favicon.ico')
def favicon():
    # Serve SVG logo as favicon
    return send_from_directory(os.path.join(app.static_folder, 'images'), 'Logo-UD.svg', mimetype='image/svg+xml')

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
    priority = db.Column(db.String(50), nullable=False)
    status = db.Column(db.String(50), default='TODO')
    
    __table_args__ = (
        db.CheckConstraint("priority IN ('low', 'medium', 'high')", name='check_task_priority'),
        db.CheckConstraint("status IN ('TODO', 'IN_PROGRESS', 'REVIEW', 'DONE')", name='check_task_status'),
    )
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

# Notification table
class Notification(db.Model):
    notification_id = db.Column(db.Integer, primary_key=True)
    recipient_id = db.Column(db.Integer, db.ForeignKey('user.user_id'), nullable=False)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.user_id'), nullable=False)
    project_id = db.Column(db.Integer, db.ForeignKey('project.project_id'), nullable=True)
    notification_type = db.Column(db.String(50), nullable=False)
    content = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    is_accepted = db.Column(db.Boolean, nullable=True)
    created_at = db.Column(db.DATE, server_default=db.func.current_date())

# Specification table
class Specification(db.Model):
    specification_id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('project.project_id'), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    objectives = db.Column(db.Text)
    requirements = db.Column(db.Text)
    constraints = db.Column(db.Text)
    deliverables = db.Column(db.Text)
    timeline = db.Column(db.Text)
    status = db.Column(db.Enum('draft', 'review', 'approved'), default='draft')
    document_path = db.Column(db.String(255))  # Path to uploaded document if any
    created_by = db.Column(db.Integer, db.ForeignKey('user.user_id'), nullable=False)
    created_at = db.Column(db.DATE, server_default=db.func.current_date())
    updated_at = db.Column(db.DATE, server_default=db.func.current_date(), onupdate=db.func.current_date())

# Message table for group chat
class Message(db.Model):
    message_id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('project.project_id'), nullable=False)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.user_id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=db.func.now())

# Ensure the database and tables are created
with app.app_context():
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

        # Send OTP to user's email using HTML format
        msg = MailMessage('Vérification OTP - Mashru3', sender=app.config['MAIL_USERNAME'], recipients=[email])
        msg.html = f"""
        <div style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <h2 style="color: #4262e2;">Bienvenue chez Mashru3!</h2>
            <p>Bonjour {name},</p>
            <p>Merci de vous être inscrit. Veuillez utiliser le code OTP suivant pour vérifier votre adresse e-mail :</p>
            <p style="font-size: 24px; font-weight: bold; color: #4262e2; text-align: center; background-color: #f0f8ff; padding: 15px; border-radius: 5px; letter-spacing: 3px;">
                {otp}
            </p>
            <p>Ce code expirera bientôt. Si vous n'avez pas demandé cette inscription, veuillez ignorer cet e-mail.</p>
            <hr style="border: none; border-top: 1px solid #eee;">
            <p style="font-size: 0.9em; color: #777;">Cordialement,<br>L'équipe Mashru3</p>
        </div>
        """
        try:
            mail.send(msg)
            return redirect(url_for('verify_otp'))
        except Exception as e:
            # Log the error and inform the user
            print(f"Error sending OTP email: {e}")
            # You might want to add a flash message here to inform the user
            return render_template('inscription.html', error="Impossible d'envoyer l'e-mail de vérification. Veuillez réessayer.")

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

@app.route('/resend_otp', methods=['POST'])
def resend_otp():
    if 'registration_data' not in session:
        return jsonify({'success': False, 'message': 'Aucune donnée d\'inscription trouvée.'}), 400

    try:
        data = session['registration_data']
        name = data['name']
        email = data['email']

        # Generate a new OTP
        otp = str(random.randint(100000, 999999))
        session['otp'] = otp # Update OTP in session

        # Resend OTP email
        msg = MailMessage('Nouveau code OTP - Mashru3', sender=app.config['MAIL_USERNAME'], recipients=[email])
        msg.html = f"""
        <div style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <h2 style="color: #4262e2;">Votre nouveau code OTP Mashru3</h2>
            <p>Bonjour {name},</p>
            <p>Voici votre nouveau code de vérification :</p>
            <p style="font-size: 24px; font-weight: bold; color: #4262e2; text-align: center; background-color: #f0f8ff; padding: 15px; border-radius: 5px; letter-spacing: 3px;">
                {otp}
            </p>
            <p>Ce code expirera bientôt. Si vous n'avez pas demandé ce code, veuillez ignorer cet e-mail.</p>
            <hr style="border: none; border-top: 1px solid #eee;">
            <p style="font-size: 0.9em; color: #777;">Cordialement,<br>L'équipe Mashru3</p>
        </div>
        """
        mail.send(msg)
        return jsonify({'success': True, 'message': 'OTP renvoyé avec succès.'})

    except Exception as e:
        print(f"Error resending OTP email: {e}")
        return jsonify({'success': False, 'message': 'Erreur lors du renvoi de l\'OTP.'}), 500

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

# Add a new context processor for user data
@app.context_processor
def inject_user_data():
    """Make user data available to all templates"""
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
        if user:
            return {
                'user_first_name': user.name,
                'user_image': user.image
            }
    return {'user_first_name': None, 'user_image': None}

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
    
    # Calculate progress for each project
    for project in user_projects:
        # Get all tasks for this project
        tasks = Task.query.filter_by(project_id=project.project_id).all()
        total_tasks = len(tasks)
        
        if total_tasks > 0:
            # Count completed tasks
            completed_tasks = Task.query.filter_by(project_id=project.project_id, status='DONE').count()
            # Calculate percentage
            project.progress = round((completed_tasks / total_tasks) * 100)
        else:
            # No tasks yet
            project.progress = 0
    
    return render_template('project.html', projects=user_projects, total_projects=total_projects)

@app.route('/add_project', methods=['GET', 'POST'])
def add_project():
    if 'user_id' not in session:
        return redirect(url_for('connexion'))
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        start_date_str = request.form['start_date']
        end_date_str = request.form['end_date']
        
        # Convert date strings to date objects
        start_date = date.fromisoformat(start_date_str) if start_date_str else None
        end_date = date.fromisoformat(end_date_str) if end_date_str else None
        
        image_path = None # Default to no image

        # Handle file upload
        if 'image' in request.files:
            file = request.files['image']
            if file and file.filename and allowed_file(file.filename):
                try:
                    # Create a secure filename
                    timestamp = int(time.time())
                    filename = secure_filename(f"project_{timestamp}_{file.filename}")
                    filepath = os.path.join(app.config['PROJECT_IMAGES_FOLDER'], filename)
                    
                    # Save the file
                    file.save(filepath)
                    
                    # Store the relative path for web access
                    image_path = f"/static/uploads/project_images/{filename}"
                except Exception as e:
                    print(f"Error uploading project image: {str(e)}") 
                    # Optionally add a flash message for the user

        new_project = Project(
            name=name, 
            description=description, 
            image=image_path, 
            start_date=start_date, 
            end_date=end_date
            # created_at is handled by server_default
        )
        db.session.add(new_project)
        db.session.commit() # Commit to get the project_id

        user_id = session['user_id']
        new_participate = Participate(
            role='Owner', 
            user_id=user_id, 
            project_id=new_project.project_id
            # created_at is handled by server_default
        )
        db.session.add(new_participate)
        db.session.commit()
        
        return redirect(url_for('projects'))
        
    # GET request just renders the template (or redirects if not logged in)
    # The modal is part of the projects page, so usually we redirect back there.
    # If accessed directly via GET (unlikely with the modal setup), redirect to projects.
    return redirect(url_for('projects'))

@app.route('/add_task', methods=['POST'])
def add_task():
    if 'user_id' not in session:
        return redirect(url_for('connexion'))
    data = request.get_json()
    
    # Convert date strings to date objects, handle empty strings
    start_date_str = data.get('start_date')
    end_date_str = data.get('end_date')
    
    start_date = date.fromisoformat(start_date_str) if start_date_str else None
    end_date = date.fromisoformat(end_date_str) if end_date_str else None
    
    new_task = Task(
        project_id=data['project_id'],
        title=data['title'],
        description=data['description'],
        priority=data['priority'],
        status=data['status'],
        start_date=start_date, # Use converted date object or None
        end_date=end_date     # Use converted date object or None
    )
    db.session.add(new_task)
    db.session.commit()

    return {'message': 'Task created successfully'}, 200

@app.route('/get_task_assignees/<int:task_id>')
def get_task_assignees(task_id):
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not authenticated'}), 401

    # Optional: Check if user has access to the project containing this task
    task = Task.query.get(task_id)
    if not task:
        return jsonify({'success': False, 'message': 'Task not found'}), 404
    
    participation = Participate.query.filter_by(
        user_id=session['user_id'],
        project_id=task.project_id
    ).first()
    if not participation:
         return jsonify({'success': False, 'message': 'Access denied to project'}), 403

    assignees = Assigned.query.filter_by(task_id=task_id).all()
    assignee_ids = [assignee.user_id for assignee in assignees]
    return jsonify({'success': True, 'assignee_ids': assignee_ids})


@app.route('/update_task_assignments', methods=['POST'])
def update_task_assignments():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not authenticated'}), 401

    data = request.get_json()
    task_id = data.get('task_id')
    submitted_user_ids = set(map(int, data.get('user_ids', [])))

    task = Task.query.get(task_id)
    if not task:
        return jsonify({'success': False, 'message': 'Task not found'}), 404

    project = Project.query.get(task.project_id)
    participation = Participate.query.filter_by(
        user_id=session['user_id'],
        project_id=task.project_id
    ).first()
    if not participation or participation.role not in ['Owner', 'Admin']:
         return jsonify({'success': False, 'message': 'Permission denied'}), 403

    assigner = User.query.get(session['user_id'])

    try:
        current_assignments = Assigned.query.filter_by(task_id=task_id).all()
        current_user_ids = set(assignment.user_id for assignment in current_assignments)

        users_to_assign = submitted_user_ids - current_user_ids
        users_to_unassign = current_user_ids - submitted_user_ids

        # Assign new users and send notifications
        for user_id in users_to_assign:
            is_participant = Participate.query.filter_by(user_id=user_id, project_id=task.project_id).first()
            if is_participant:
                new_assignment = Assigned(user_id=user_id, task_id=task_id) 
                db.session.add(new_assignment)

                # Create notification for the newly assigned user
                notification_content = f"{assigner.name} vous a assigné à la tâche '{task.title}' dans le projet '{project.name}'."
                
                new_notification = Notification(
                    recipient_id=user_id,
                    sender_id=session['user_id'],
                    project_id=task.project_id,
                    notification_type='task_assignment',
                    content=notification_content,
                    is_read=False
                )
                db.session.add(new_notification)

        # Unassign users and send notifications
        if users_to_unassign:
            # Perform the deletion
            Assigned.query.filter(
                Assigned.task_id == task_id,
                Assigned.user_id.in_(users_to_unassign)
            ).delete(synchronize_session=False)

            # Create notifications for unassigned users
            for user_id in users_to_unassign:
                # Check if user still exists (optional, but good practice)
                unassigned_user = User.query.get(user_id)
                if unassigned_user:
                    notification_content = f"{assigner.name} vous a désassigné de la tâche '{task.title}' dans le projet '{project.name}'."
                    
                    unassign_notification = Notification(
                        recipient_id=user_id,
                        sender_id=session['user_id'],
                        project_id=task.project_id,
                        notification_type='task_unassignment', # New type
                        content=notification_content,
                        is_read=False
                    )
                    db.session.add(unassign_notification)

        db.session.commit()
        return jsonify({'success': True, 'message': 'Assignments updated successfully'})

    except Exception as e:
        db.session.rollback()
        print(f"Error updating assignments for task {task_id}: {str(e)}")
        return jsonify({'success': False, 'message': 'An error occurred while updating assignments.'}), 500

@app.route('/add_member', methods=['POST'])
def add_member():
    if 'user_id' not in session:
        return redirect(url_for('connexion'))
    data = request.get_json()
    user = User.query.filter_by(email=data['email']).first()
    if user:
        # Check if user is already a member of the project
        existing_participation = Participate.query.filter_by(
            user_id=user.user_id,
            project_id=data['project_id']
        ).first()
        
        # Check if there's already a pending invitation
        existing_invitation = Notification.query.filter_by(
            recipient_id=user.user_id,
            project_id=data['project_id'],
            notification_type='invitation',
            is_accepted=None
        ).first()
        
        if existing_participation:
            return {'message': 'Cet utilisateur est déjà membre de ce projet'}, 400
        elif existing_invitation:
            return {'message': 'Une invitation a déjà été envoyée à cet utilisateur pour ce projet'}, 400
        else:
            # Get project and sender information
            project = Project.query.get(data['project_id'])
            sender = User.query.get(session['user_id'])
            
            # Map English role to French for notification message
            role_en = data['role']
            role_fr_map = {
                'Owner': 'Propriétaire',
                'Admin': 'Administrateur',
                'Member': 'Membre'
            }
            role_fr = role_fr_map.get(role_en, role_en) # Fallback to English if not found

            # Create a notification (invitation)
            new_notification = Notification(
                recipient_id=user.user_id,
                sender_id=session['user_id'],
                project_id=data['project_id'],
                notification_type='invitation',
                # Use French role in the content
                content=f"{sender.name} vous a invité à rejoindre le projet '{project.name}' en tant que {role_fr}.",
                is_read=False,
                is_accepted=None  # Pending
            )
            
            # Store the role in the content as JSON or in a separate column if needed
            # For now, adding it to the content message
            
            db.session.add(new_notification)
            db.session.commit()
            
            # Send an email notification if needed (optional)
            try:
                msg = MailMessage('Invitation à rejoindre un projet Mashru3', 
                              sender=app.config['MAIL_USERNAME'], 
                              recipients=[user.email])
                # Use French role in email as well
                msg.body = f"""
                Bonjour {user.name},
                
                {sender.name} vous a invité à rejoindre le projet '{project.name}' en tant que {role_fr}.
                
                Connectez-vous à votre compte Mashru3 pour accepter ou refuser cette invitation.
                
                Cordialement,
                L'équipe Mashru3
                """
                mail.send(msg)
            except Exception as e:
                print(f"Error sending invitation email: {str(e)}")
                # Don't fail the whole request if email fails, but log it.
                
            return {'message': 'Invitation sent successfully'}, 200
    else:
        return {'message': 'Utilisateur non trouvé avec cet e-mail'}, 404

@app.route('/notifications')
def notifications():
    if 'user_id' not in session:
        return redirect(url_for('connexion'))
    
    user_id = session['user_id']
    notifications = Notification.query.filter_by(recipient_id=user_id).order_by(Notification.created_at.desc()).all()
    
    # For each notification, get sender and project information
    for notification in notifications:
        notification.sender = User.query.get(notification.sender_id)
        if notification.project_id:
            notification.project = Project.query.get(notification.project_id)
    
    return render_template('notifications.html', notifications=notifications)

@app.route('/notification_count')
def notification_count():
    if 'user_id' not in session:
        return jsonify({'count': 0}), 401
    
    user_id = session['user_id']
    count = Notification.query.filter_by(recipient_id=user_id, is_read=False).count()
    
    return jsonify({'count': count})

@app.route('/respond_invitation', methods=['POST'])
def respond_invitation():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not authenticated'}), 401
    
    data = request.get_json()
    notification_id = data.get('notification_id')
    response = data.get('response')  # 'accept' or 'reject'
    
    notification = Notification.query.get(notification_id)
    
    if not notification or notification.recipient_id != session['user_id']:
        return jsonify({'success': False, 'message': 'Invitation not found or not authorized'}), 404
    
    if notification.notification_type != 'invitation' or notification.is_accepted is not None:
        return jsonify({'success': False, 'message': 'Invalid invitation status'}), 400
    
    try:
        if response == 'accept':
            # Extract role from notification content (best effort)
            # This is fragile. Ideally, store the role ('Owner', 'Admin', 'Member') 
            # in a separate field or reliably encoded in the content.
            role_fr_map_reverse = {
                'Propriétaire': 'Owner',
                'Administrateur': 'Admin',
                'Membre': 'Member'
            }
            role_en = 'Member' # Default role
            try:
                role_fr = notification.content.split(' en tant que ')[-1].replace('.', '')
                role_en = role_fr_map_reverse.get(role_fr, 'Member') # Default to Member if extraction/mapping fails
            except:
                 pass # Keep default 'Member' if splitting fails

            # Add user to project with the determined English role
            new_participate = Participate(
                user_id=notification.recipient_id,
                project_id=notification.project_id,
                role=role_en # Use the determined English role
            )
            db.session.add(new_participate)
            notification.is_accepted = True
            
        else:  # reject
            notification.is_accepted = False
        
        notification.is_read = True
        db.session.commit()
        
        return jsonify({'success': True, 'message': f'Invitation {response}ed successfully'})
    
    except Exception as e:
        db.session.rollback()
        print(f"Error responding to invitation: {str(e)}") # Log the error
        return jsonify({'success': False, 'message': 'An error occurred while processing the invitation.'}), 500

@app.route('/mark_notification_read/<int:notification_id>', methods=['POST'])
def mark_notification_read(notification_id):
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not authenticated'}), 401
    
    notification = Notification.query.get(notification_id)
    
    if not notification or notification.recipient_id != session['user_id']:
        return jsonify({'success': False, 'message': 'Notification not found or not authorized'}), 404
    
    try:
        notification.is_read = True
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

# Add notification data to user context
@app.context_processor
def inject_notifications_data():
    """Add notification count to all templates"""
    if 'user_id' in session:
        unread_count = Notification.query.filter_by(
            recipient_id=session['user_id'], 
            is_read=False
        ).count()
        return {'notification_count': unread_count}
    return {'notification_count': 0}

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
    participants = [{'name': user.name, 'email': user.email, 'user_id': user.user_id, 'role': role} for user, role in participants_data]
    
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

    # Get pending invitations for this project
    pending_invitations = db.session.query(
        Notification, User.email, User.name
    ).join(
        User, Notification.recipient_id == User.user_id
    ).filter(
        Notification.project_id == project_id,
        Notification.notification_type == 'invitation',
        Notification.is_accepted == None
    ).all()

    # Format pending invitations data
    pending_invites_data = []
    for notification, email, name in pending_invitations:
        # Extract role from content (assuming format: "... as Role.")
        role_str = notification.content.split(' en tant que ')[-1].replace('.', '') if ' en tant que ' in notification.content else 'N/A'
        pending_invites_data.append({
            'email': email,
            'name': name,
            'role': role_str,
            'sent_at': notification.created_at
        })

    return render_template(
        'project_detail.html', 
        project=project, 
        participants=participants, 
        tasks=tasks, 
        user_role=user_role,
        is_admin=is_admin,
        pending_invitations=pending_invites_data
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
        project = Project.query.get_or_404(project_id)
        old_image_path = project.image # Store the old image path
        
        # Handle form data
        if request.files and 'project_image' in request.files:
            file = request.files['project_image']
            if file and file.filename and allowed_file(file.filename):
                # Create secure filename and save the file
                timestamp = int(time.time()) # Add timestamp for uniqueness
                filename = secure_filename(f"project_{project_id}_{timestamp}_{file.filename}")
                filepath = os.path.join(app.config['PROJECT_IMAGES_FOLDER'], filename)
                file.save(filepath)
                
                # Update project image path
                relative_path = f"/static/uploads/project_images/{filename}"
                project.image = relative_path

                # Delete the old image file if it exists and is different
                if old_image_path and old_image_path != relative_path:
                    try:
                        # Construct the absolute path for the old image
                        old_image_full_path = os.path.join(app.root_path, old_image_path.lstrip('/'))
                        if os.path.exists(old_image_full_path):
                            os.remove(old_image_full_path)
                            print(f"Deleted old project image: {old_image_full_path}") # Optional: for logging
                    except Exception as e:
                        print(f"Error deleting old project image {old_image_path}: {str(e)}") # Log error but continue
        
        # Update other project data
        if request.form.get('name'):
            project.name = request.form.get('name')
        if request.form.get('description'):
            project.description = request.form.get('description')
        if request.form.get('start_date'):
            project.start_date = date.fromisoformat(request.form.get('start_date'))
        if request.form.get('end_date'):
            project.end_date = date.fromisoformat(request.form.get('end_date'))
            
        db.session.commit()
        
        # Return success response with updated image path if applicable
        response = {'success': True, 'message': 'Project updated successfully'}
        if project.image:
            response['image_path'] = project.image
            
        return jsonify(response)
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
    new_role = data.get('role') # Expecting 'Owner', 'Admin', 'Member' from frontend
    
    # Basic validation for expected roles
    if new_role not in ['Owner', 'Admin', 'Member']:
         return jsonify({'success': False, 'message': 'Invalid role specified'}), 400

    # Check if current user has permission (based on English roles)
    current_user_participation = Participate.query.filter_by(
        user_id=session['user_id'],
        project_id=project_id
    ).first()
    
    if not current_user_participation or current_user_participation.role not in ['Owner', 'Admin']:
        return jsonify({'success': False, 'message': 'Permission denied'}), 403
    
    # Check if target user exists and is part of the project
    target_participation = Participate.query.filter_by(
        user_id=target_user_id,
        project_id=project_id
    ).first()

    if not target_participation:
        return jsonify({'success': False, 'message': 'Target user not found in this project'}), 404
    
    # Prevent non-owners from changing the owner's role or making someone else owner
    if (target_participation.role == 'Owner' or new_role == 'Owner') and current_user_participation.role != 'Owner':
        return jsonify({'success': False, 'message': 'Only the project owner can manage ownership'}), 403
    
    # Prevent owner from changing their own role if they are the only owner
    if target_participation.role == 'Owner' and int(target_user_id) == session['user_id']:
        owner_count = Participate.query.filter_by(project_id=project_id, role='Owner').count()
        if owner_count <= 1:
             return jsonify({'success': False, 'message': 'Cannot change role, you are the only owner'}), 403

    try:
        target_participation.role = new_role # Update with English role
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

    if not target_participation:
         return jsonify({'success': False, 'message': 'Member not found in project'}), 404

    if target_participation.role == 'Owner':
        return jsonify({'success': False, 'message': 'Cannot remove project owner'}), 403

    # Prevent self-removal
    if int(target_user_id) == session['user_id']:
        return jsonify({'success': False, 'message': 'Cannot remove yourself from the project'}), 400

    try:
        # Get project and remover details for notification
        project = Project.query.get(project_id)
        remover = User.query.get(session['user_id'])

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

        # Create notification for the removed user
        removal_notification = Notification(
            recipient_id=target_user_id,
            sender_id=session['user_id'],
            project_id=project_id,
            notification_type='removal',
            content=f"Vous avez été retiré du projet '{project.name}' par {remover.name}.",
            is_read=False
        )
        db.session.add(removal_notification)

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
            
            # Handle profile picture upload
            if 'profile_picture' in request.files:
                file = request.files['profile_picture']
                if file and file.filename:
                    if allowed_file(file.filename):
                        try:
                            # Create a secure filename and save the file
                            filename = secure_filename(f"user_{user_id}_{file.filename}")
                            filepath = os.path.join(app.config['PROFILE_PICS_FOLDER'], filename)
                            file.save(filepath)
                            
                            # Update the user's profile image path in the database
                            relative_path = f"/static/uploads/profile_pics/{filename}"
                            user.image = relative_path
                        except Exception as e:
                            error_message = f"Erreur lors du téléchargement de l'image: {str(e)}"
                    else:
                        error_message = "Format d'image non supporté. Utilisez JPG, PNG ou GIF."
            
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
    
    return render_template('parametre.html', user=user, success_message=success_message, error_message=error_message)

@app.route('/deconnexion', methods=['POST'])
def deconnexion():
    # Clear the user's session
    session.pop('user_id', None)
    return redirect(url_for('connexion'))

@app.route('/')
def home():
    # If user is logged in, redirect to dashboard
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    # Otherwise show the landing page
    return render_template('landing.html')

@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form['email']
        user = User.query.filter_by(email=email).first()
        
        if user:
            # Generate a reset token (a random string)
            reset_token = ''.join(random.choices('0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ', k=32))
            # Store the token in the session with an expiration time
            session[f'reset_token_{email}'] = {
                'token': reset_token,
                'expiry': (datetime.now() + timedelta(hours=1)).timestamp()
            }
            
            # Create the reset link
            reset_link = url_for('reset_password', token=reset_token, email=email, _external=True)
            
            # Send the email
            try:
                msg = MailMessage('Réinitialisation de mot de passe', 
                              sender=app.config['MAIL_USERNAME'], 
                              recipients=[email])
                msg.body = f'''Pour réinitialiser votre mot de passe, veuillez cliquer sur le lien suivant:
                
{reset_link}

Si vous n'avez pas demandé de réinitialisation de mot de passe, veuillez ignorer ce message.

Ce lien expirera dans 1 heure.
'''
                mail.send(msg)
                return render_template('forgot_password.html', 
                                      success_message="Un email de réinitialisation a été envoyé à votre adresse email.")
            except Exception as e:
                print(f"Error sending email: {str(e)}")
                return render_template('forgot_password.html', 
                                      error_message="Impossible d'envoyer l'email. Veuillez réessayer plus tard.")
        else:
            # Even if the user doesn't exist, we return a success message for security
            return render_template('forgot_password.html', 
                                 success_message="Si cette adresse email existe dans notre base de données, un email de réinitialisation a été envoyé.")
            
    return render_template('forgot_password.html')

@app.route('/reset_password', methods=['GET', 'POST'])
def reset_password():
    token = request.args.get('token')
    email = request.args.get('email')
    
    # Check if token is valid
    token_data = session.get(f'reset_token_{email}')
    if not token_data or token_data.get('token') != token or token_data.get('expiry') < datetime.now().timestamp():
        return render_template('reset_password.html', 
                             error_message="Ce lien de réinitialisation est invalide ou a expiré.")
    
    if request.method == 'POST':
        new_password = request.form['new_password']
        confirm_password = request.form['confirm_password']
        
        if new_password != confirm_password:
            return render_template('reset_password.html', 
                                 error_message="Les mots de passe ne correspondent pas.",
                                 token=token,
                                 email=email)
        
        user = User.query.filter_by(email=email).first()
        if user:
            user.password = generate_password_hash(new_password)
            db.session.commit()
            
            # Clear the reset token
            session.pop(f'reset_token_{email}', None)
            
            return redirect(url_for('connexion', reset_success=True))
    
    return render_template('reset_password.html', token=token, email=email)

@app.route('/calendrier')
def calendrier():
    if 'user_id' not in session:
        return redirect(url_for('connexion'))
    
    user_id = session['user_id']
    
    # Get all projects the user participates in
    projects = db.session.query(Project).join(Participate).filter(
        Participate.user_id == user_id
    ).all()
    
    return render_template('calendrier.html', projects=projects)

@app.route('/get_calendar_events')
def get_calendar_events():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not authenticated'}), 401
    
    user_id = session['user_id']
    start_date = request.args.get('start')
    end_date = request.args.get('end')
    project_id = request.args.get('project', 'all')
    priorities = request.args.get('priorities', 'high,medium,low').split(',')
    
    # Get projects the user is part of
    user_projects_query = db.session.query(Project.project_id).join(Participate).filter(
        Participate.user_id == user_id
    )
    
    # Base query for tasks
    query = db.session.query(Task, Project.name.label('project_name')).join(
        Project, Task.project_id == Project.project_id
    )
    
    # Filter by user's projects 
    query = query.filter(Task.project_id.in_(user_projects_query))
    
    # Filter by specific project if requested
    if project_id != 'all':
        query = query.filter(Task.project_id == project_id)
    
    # Filter by priority
    if priorities:
        query = query.filter(Task.priority.in_(priorities))
    
    # Filter tasks within date range or without end date
    if start_date and end_date:
        # Tasks that overlap with the requested date range
        query = query.filter(
            db.or_(
                # Tasks that end within or after the range
                db.and_(
                    Task.start_date != None,
                    Task.end_date != None,
                    db.or_(
                        db.and_(Task.start_date <= end_date, Task.end_date >= start_date),
                        db.and_(Task.start_date <= end_date, Task.end_date == None)
                    )
                ),
                # Tasks without specific dates
                db.and_(Task.start_date == None, Task.end_date == None)
            )
        )
    
    tasks = query.all()
    
    events = []
    for task, project_name in tasks:
        # Get assignees for this task
        assignees = db.session.query(User).join(Assigned).filter(
            Assigned.task_id == task.task_id
        ).all()
        
        assignee_list = [{'id': user.user_id, 'name': user.name} for user in assignees]
        
        event = {
            'id': task.task_id,
            'title': task.title,
            'start': task.start_date.isoformat() if task.start_date else None,
            'end': task.end_date.isoformat() if task.end_date else None,
            'description': task.description,
            'priority': task.priority,
            'status': task.status,
            'projectId': task.project_id,
            'projectName': project_name,
            'assignees': assignee_list
        }
        events.append(event)
    
    return jsonify({'success': True, 'events': events})

@app.route('/groupes')
def groupes():
    if 'user_id' not in session:
        return redirect(url_for('connexion'))
    
    user_id = session['user_id']
    # Fetch user's projects for sidebar
    user_projects = db.session.query(Project).join(Participate).filter(
        Participate.user_id == user_id
    ).all()
    return render_template('messagerie.html', projects=user_projects)

# API endpoint: Get user's projects (for sidebar)
@app.route('/api/user_projects')
def api_user_projects():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not authenticated'}), 401
    user_id = session['user_id']
    projects = db.session.query(Project).join(Participate).filter(
        Participate.user_id == user_id
    ).all()
    result = [{'project_id': p.project_id, 'name': p.name} for p in projects]
    return jsonify({'success': True, 'projects': result})

# API endpoint: Get messages for a project
@app.route('/api/messages/<int:project_id>')
def api_get_messages(project_id):
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not authenticated'}), 401
    # Check user is a participant
    participation = Participate.query.filter_by(
        user_id=session['user_id'],
        project_id=project_id
    ).first()
    if not participation:
        return jsonify({'success': False, 'message': 'Access denied'}), 403
    messages = Message.query.filter_by(project_id=project_id).order_by(Message.timestamp.asc()).all()
    result = []
    for msg in messages:
        sender = User.query.get(msg.sender_id)
        result.append({
            'message_id': msg.message_id,
            'sender_id': msg.sender_id,
            'sender_name': sender.name if sender else "Utilisateur",
            'content': msg.content,
            'timestamp': msg.timestamp.strftime('%H:%M')
        })
    return jsonify({'success': True, 'messages': result})

# API endpoint: Send a message
@app.route('/api/send_message', methods=['POST'])
def api_send_message():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not authenticated'}), 401
    data = request.get_json()
    project_id = data.get('project_id')
    content = data.get('content', '').strip()
    if not project_id or not content:
        return jsonify({'success': False, 'message': 'Project and content required'}), 400
    # Check user is a participant
    participation = Participate.query.filter_by(
        user_id=session['user_id'],
        project_id=project_id
    ).first()
    if not participation:
        return jsonify({'success': False, 'message': 'Access denied'}), 403
    msg = Message(
        project_id=project_id,
        sender_id=session['user_id'],
        content=content
    )
    db.session.add(msg)
    db.session.commit()
    sender = User.query.get(session['user_id'])
    return jsonify({
        'success': True,
        'message': {
            'message_id': msg.message_id,
            'sender_id': msg.sender_id,
            'sender_name': sender.name if sender else "Vous",
            'content': msg.content,
            'timestamp': msg.timestamp.strftime('%H:%M')
        }
    })

@app.route('/specifications')
def specifications():
    if 'user_id' not in session:
        return redirect(url_for('connexion'))
    
    user_id = session['user_id']
    
    # Get user's projects for the dropdown menu
    user_projects = db.session.query(Project).join(Participate).filter(
        Participate.user_id == user_id
    ).all()
    
    # Get existing specifications for the user's projects
    project_ids = [project.project_id for project in user_projects]
    
    specifications_list = []
    if project_ids:
        specifications_list = Specification.query.filter(
            Specification.project_id.in_(project_ids)
        ).order_by(Specification.updated_at.desc()).all()
        
        # Add project name to each specification
        for spec in specifications_list:
            project = Project.query.get(spec.project_id)
            if project:
                spec.project_name = project.name
    
    return render_template('specifications.html', projects=user_projects, specifications=specifications_list)

@app.route('/save_specification', methods=['POST'])
def save_specification():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not authenticated'}), 401
    
    try:
        # Get form data
        data = request.form
        project_id = data.get('project_id')
        title = data.get('title')
        
        # Validate required fields
        if not project_id or not title:
            return jsonify({
                'success': False, 
                'message': 'Le projet et le titre sont requis'
            }), 400
        
        # Check if the user has access to this project
        participation = Participate.query.filter_by(
            user_id=session['user_id'],
            project_id=project_id
        ).first()
        
        if not participation:
            return jsonify({
                'success': False, 
                'message': 'Vous n\'avez pas accès à ce projet'
            }), 403
            
        # Create new specification
        new_specification = Specification(
            project_id=project_id,
            title=title,
            description=data.get('description', ''),
            objectives=data.get('objectives', ''),
            requirements=data.get('requirements', ''),
            constraints=data.get('constraints', ''),
            deliverables=data.get('deliverables', ''),
            timeline=data.get('timeline', ''),
            status=data.get('status', 'draft'),
            created_by=session['user_id']
        )
        
        # Handle file upload if provided
        if 'document' in request.files:
            file = request.files['document']
            if file and file.filename:
                # Create uploads directory for specifications if it doesn't exist
                spec_dir = os.path.join(app.config['UPLOAD_FOLDER'], 'specifications')
                os.makedirs(spec_dir, exist_ok=True)
                
                # Save the file
                filename = secure_filename(f"spec_{int(time.time())}_{file.filename}")
                filepath = os.path.join(spec_dir, filename)
                file.save(filepath)
                
                # Update specification with document path
                new_specification.document_path = f"/static/uploads/specifications/{filename}"
        
        db.session.add(new_specification)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Cahier des charges enregistré avec succès',
            'specification_id': new_specification.specification_id
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Erreur lors de l\'enregistrement: {str(e)}'
        }), 500

# New route to generate spec content via AI
@app.route('/generate_spec_content', methods=['POST'])
def generate_spec_content():
    data = request.get_json() or {}
    description = data.get('description', '')
    if not description:
        return jsonify({'success': False, 'message': 'Description manquante'}), 400
    try:
        # Call OpenAI ChatCompletion
        prompt = (
            "Vous êtes un assistant qui génère un cahier des charges structuré à partir d'une description de projet. "
            "Répondez strictement par un objet JSON avec les clés: description, objectives, requirements, constraints, deliverables, timeline."
        )
        response = openai.chat.completions.create(
            model='gpt-3.5-turbo',
            messages=[
                {'role': 'system', 'content': prompt},
                {'role': 'user', 'content': description}
            ],
            temperature=0.7,
            max_tokens=800
        )
        content = response.choices[0].message.content.strip()
        # Parse JSON
        import json
        result = json.loads(content)
        return jsonify({'success': True, **result})
    except Exception as e:
        return jsonify({'success': False, 'message': f'Erreur IA: {str(e)}'}), 500

@app.route('/specification/<int:specification_id>')
def view_specification(specification_id):
    if 'user_id' not in session:
        return redirect(url_for('connexion'))
    
    specification = Specification.query.get_or_404(specification_id)
    
    # Check if user has access to the project
    participation = Participate.query.filter_by(
        user_id=session['user_id'],
        project_id=specification.project_id
    ).first()
    
    if not participation:
        return "Vous n'avez pas accès à ce cahier des charges", 403
    
    # Get project info
    project = Project.query.get(specification.project_id)
    
    return render_template('view_specification.html', 
                          specification=specification, 
                          project=project)

@app.route('/edit_specification/<int:specification_id>')
def edit_specification(specification_id):
    if 'user_id' not in session:
        return redirect(url_for('connexion'))
    
    specification = Specification.query.get_or_404(specification_id)
    
    # Check if user has access to the project and spec is in draft mode
    participation = Participate.query.filter_by(
        user_id=session['user_id'],
        project_id=specification.project_id
    ).first()
    
    if not participation:
        return "Vous n'avez pas accès à ce cahier des charges", 403
    
    if specification.status != 'draft':
        return "Seuls les cahiers des charges en mode brouillon peuvent être modifiés", 403
    
    # Get project info for the form
    project = Project.query.get(specification.project_id)
    
    # Get all projects the user has access to (for the project selector)
    user_projects = db.session.query(Project).join(Participate).filter(
        Participate.user_id == session['user_id']
    ).all()
    
    
    return render_template('edit_specification.html', 
                          specification=specification, 
                          project=project,
                          projects=user_projects)

@app.route('/delete_specification/<int:specification_id>', methods=['POST'])
def delete_specification(specification_id):
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Non authentifié'}), 401
    
    specification = Specification.query.get_or_404(specification_id)
    
    # Vérifier si l'utilisateur a accès au projet
    participation = Participate.query.filter_by(
        user_id=session['user_id'],
        project_id=specification.project_id
    ).first()
    
    if not participation:
        return jsonify({'success': False, 'message': 'Vous n\'avez pas accès à ce cahier des charges'}), 403
    
    # Seuls le créateur, le propriétaire du projet ou un admin peuvent supprimer
    if specification.created_by != session['user_id'] and participation.role not in ['Owner', 'Admin']:
        return jsonify({'success': False, 'message': 'Vous n\'avez pas les droits pour supprimer ce document'}), 403
    
    try:
        # Supprimer le document associé si existant
        if specification.document_path:
            document_path = os.path.join(app.root_path, 'static', specification.document_path.lstrip('/static/'))
            if os.path.exists(document_path):
                os.remove(document_path)
        
        # Supprimer la spécification
        db.session.delete(specification)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Cahier des charges supprimé avec succès'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Erreur lors de la suppression: {str(e)}'}), 500

@app.route('/update_specification/<int:specification_id>', methods=['POST'])
def update_specification(specification_id):
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Non authentifié'}), 401
    
    specification = Specification.query.get_or_404(specification_id)
    
    # Vérifier si l'utilisateur a accès au projet
    participation = Participate.query.filter_by(
        user_id=session['user_id'],
        project_id=specification.project_id
    ).first()
    
    if not participation:
        return jsonify({'success': False, 'message': 'Vous n\'avez pas accès à ce cahier des charges'}), 403
    
    # Seuls le créateur, le propriétaire du projet ou un admin peuvent modifier
    if specification.created_by != session['user_id'] and participation.role not in ['Owner', 'Admin']:
        return jsonify({'success': False, 'message': 'Vous n\'avez pas les droits pour modifier ce document'}), 403
    
    # Seul un cahier en mode brouillon peut être modifié
    if specification.status != 'draft' and specification.created_by != session['user_id'] and participation.role != 'Owner':
        return jsonify({'success': False, 'message': 'Seuls les cahiers des charges en mode brouillon peuvent être modifiés'}), 403
    
    try:
        # Récupérer les données du formulaire
        data = request.form
        
        # Mettre à jour les champs de la spécification
        specification.title = data.get('title', specification.title)
        specification.description = data.get('description', specification.description)
        specification.objectives = data.get('objectives', specification.objectives)
        specification.requirements = data.get('requirements', specification.requirements)
        specification.constraints = data.get('constraints', specification.constraints)
        specification.deliverables = data.get('deliverables', specification.deliverables)
        specification.timeline = data.get('timeline', specification.timeline)
        specification.status = data.get('status', specification.status)
        
        # Gérer le téléchargement du document s'il est fourni
        if 'document' in request.files:
            file = request.files['document']
            if file and file.filename:
                # Supprimer l'ancien document s'il existe
                if specification.document_path:
                    old_document_path = os.path.join(app.root_path, 'static', specification.document_path.lstrip('/static/'))
                    if os.path.exists(old_document_path):
                        os.remove(old_document_path)
                
                # Créer le répertoire pour les spécifications s'il n'existe pas
                spec_dir = os.path.join(app.config['UPLOAD_FOLDER'], 'specifications')
                os.makedirs(spec_dir, exist_ok=True)
                
                # Enregistrer le nouveau fichier
                filename = secure_filename(f"spec_{specification_id}_{int(time.time())}_{file.filename}")
                filepath = os.path.join(spec_dir, filename)
                file.save(filepath)
                
                # Mettre à jour le chemin du document
                specification.document_path = f"/static/uploads/specifications/{filename}"
        
        # Mettre à jour la date de modification est automatique grâce à onupdate
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Cahier des charges mis à jour avec succès'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Erreur lors de la mise à jour: {str(e)}'}), 500

@app.route('/delete_all_notifications', methods=['POST'])
def delete_all_notifications():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Non authentifié'}), 401
    
    user_id = session['user_id']
    
    try:
        # Delete all notifications for the current user
        Notification.query.filter_by(recipient_id=user_id).delete()
        db.session.commit()
        return jsonify({'success': True, 'message': 'Toutes les notifications ont été supprimées.'})
    except Exception as e:
        db.session.rollback()
        print(f"Error deleting all notifications for user {user_id}: {str(e)}") # Log the error
        return jsonify({'success': False, 'message': 'Une erreur est survenue lors de la suppression.'}), 500

@app.route('/diagnostic')
def diagnostic():
    import os
    import sys
    import platform
    import flask
    
    # Liste des fichiers de templates importants
    template_files = [
        'base.html',
        'dashboard.html',
        'connexion.html',
        'project.html',
        'notifications.html',
        'parametre.html'
    ]
    
    templates = []
    template_dir = os.path.join(app.root_path, 'templates')
    
    for file in template_files:
        file_path = os.path.join(template_dir, file)
        exists = os.path.exists(file_path)
        size = os.path.getsize(file_path) if exists else None
        templates.append({
            'name': file,
            'exists': exists,
            'size': size
        })
    
    # Vérification de la connexion à la base de données
    db_status = {'connected': False, 'tables': []}
    try:
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="",
            database="Mashru3"
        )
        cursor = conn.cursor()
        cursor.execute("SHOW TABLES")
        db_status['connected'] = True
        db_status['tables'] = [table[0] for table in cursor.fetchall()]
        conn.close()
    except Exception as e:
        db_status['error'] = str(e)
    
    # Informations système
    system_info = {
        'python_version': sys.version,
        'flask_version': flask.__version__,
        'os': platform.platform()
    }
    
    return render_template(
        'debug.html', 
        templates=templates,
        config=str(app.config),
        db_status=db_status,
        system_info=system_info
    )

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, port=port, host="0.0.0.0")
