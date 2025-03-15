from flask import Flask, render_template, redirect, url_for, request, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import date
import mysql.connector
from email.message import EmailMessage
from flask_mail import Mail, Message

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:@localhost/Mashru3'
app.config['SECRET_KEY'] = 'your_secret_key'
db = SQLAlchemy(app)

# Configure Flask-Mail for Gmail
app.config['MAIL_SERVER'] = 'smtp.gmail.com'  # Gmail SMTP server
app.config['MAIL_PORT'] = 587  # Port for TLS
app.config['MAIL_USERNAME'] = 'mashru3.djib@gmail.com'  # Replace with your Gmail address
app.config['MAIL_PASSWORD'] = ''  # Replace with your app password (not your Gmail password)
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

@app.context_processor
def inject_user():
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
        if user:
            return {
                'user_first_name': user.name,
                'user_image': user.image
            }
    return {
        'user_first_name': None,
        'user_image': None
    }

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
        new_user = User(name=name, email=email, password=password)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('connexion'))
    return render_template('inscription.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('connexion'))
    
    user_id = session['user_id']
    user = User.query.get(user_id)
    
    # Get user's projects
    user_projects = db.session.query(Project).join(Participate).filter(Participate.user_id == user_id).all()
    active_projects = len(user_projects)
    
    # Get tasks statistics
    tasks_query = db.session.query(Task).join(Project).join(Participate).filter(
        Participate.user_id == user_id,
        Participate.project_id == Project.project_id,
        Task.project_id == Project.project_id
    )
    
    total_tasks = tasks_query.count()
    todo_tasks = tasks_query.filter(Task.status == 'TODO').count()
    in_progress_tasks = tasks_query.filter(Task.status == 'IN_PROGRESS').count()
    review_tasks = tasks_query.filter(Task.status == 'REVIEW').count()
    done_tasks = tasks_query.filter(Task.status == 'DONE').count()
    completed_tasks = done_tasks
    
    # Get project names and task counts for the chart
    project_data = db.session.query(
        Project.name, 
        db.func.count(Task.task_id)
    ).join(Task, Project.project_id == Task.project_id)\
     .join(Participate, Project.project_id == Participate.project_id)\
     .filter(Participate.user_id == user_id)\
     .group_by(Project.name)\
     .all()
    
    project_names = [p[0] for p in project_data] if project_data else []
    project_tasks = [p[1] for p in project_data] if project_data else []
    
    return render_template(
        'dashboard.html', 
        user_first_name=user.name,
        user_image=user.image,
        total_tasks=total_tasks,
        completed_tasks=completed_tasks,
        active_projects=active_projects,
        todo_tasks=todo_tasks,
        in_progress_tasks=in_progress_tasks,
        review_tasks=review_tasks,
        done_tasks=done_tasks,
        project_names=project_names,
        project_tasks=project_tasks
    )

# Updated projects route to handle pagination correctly
@app.route('/projects')
def projects():
    if 'user_id' not in session:
        return redirect(url_for('connexion'))
    user_id = session['user_id']
    user_projects = db.session.query(Project).join(Participate).filter(Participate.user_id == user_id).all()
    total_projects = len(user_projects)
    
    # Add pagination parameters
    page = request.args.get('page', 1, type=int)
    per_page = 8
    offset = (page - 1) * per_page
    
    # Paginate projects
    paginated_projects = user_projects[offset:offset+per_page]
    
    # Calculate next and prev urls
    next_url = url_for('projects', page=page + 1) if offset + per_page < total_projects else None
    prev_url = url_for('projects', page=page - 1) if page > 1 else None
    
    return render_template('project.html', 
                          projects=paginated_projects, 
                          total_projects=total_projects,
                          current_page=page,
                          next_url=next_url,
                          prev_url=prev_url)

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

@app.route('/update_project/<int:project_id>', methods=['POST'])
def update_project(project_id):
    if 'user_id' not in session:
        return redirect(url_for('connexion'))
    
    user_id = session['user_id']
    
    # Check if user is a participant in this project
    participation = Participate.query.filter_by(
        user_id=user_id,
        project_id=project_id
    ).first()
    
    if not participation or participation.role != 'Owner':
        # Only project owners can edit project details
        return "Unauthorized", 403
    
    project = Project.query.get_or_404(project_id)
    
    # Update project details
    project.name = request.form['name']
    project.description = request.form['description']
    project.image = request.form['image']
    
    # Handle dates
    if request.form['start_date']:
        project.start_date = request.form['start_date']
    else:
        project.start_date = None
        
    if request.form['end_date']:
        project.end_date = request.form['end_date']
    else:
        project.end_date = None
    
    # Handle project status
    if request.form.get('status') == 'completed':
        if 'finished_date' in request.form and request.form['finished_date']:
            project.finished_date = request.form['finished_date']
        else:
            project.finished_date = date.today()
    else:
        project.finished_date = None
    
    db.session.commit()
    return redirect(url_for('project_detail', project_id=project_id))

@app.route('/delete_project/<int:project_id>', methods=['POST'])
def delete_project(project_id):
    if 'user_id' not in session:
        return redirect(url_for('connexion'))
    
    user_id = session['user_id']
    
    # Check if user is the project owner
    participation = Participate.query.filter_by(
        user_id=user_id,
        project_id=project_id,
        role='Owner'
    ).first()
    
    if not participation:
        return "Unauthorized", 403
    
    project = Project.query.get_or_404(project_id)
    
    # Delete all tasks associated with the project
    tasks = Task.query.filter_by(project_id=project_id).all()
    for task in tasks:
        # Delete task assignments
        Assigned.query.filter_by(task_id=task.task_id).delete()
        
        # Delete task predecessors
        Predecessor.query.filter_by(task_id=task.task_id).delete()
        Predecessor.query.filter_by(predecessor_id=task.task_id).delete()
        
        # Delete the task
        db.session.delete(task)
    
    # Delete all participations
    Participate.query.filter_by(project_id=project_id).delete()
    
    # Delete the project
    db.session.delete(project)
    db.session.commit()
    
    return redirect(url_for('projects'))

@app.route('/logout')
def logout():
    session.clear()  # Session ends here
    return redirect(url_for('connexion'))

@app.route('/')
def home():
    return redirect(url_for('dashboard'))

@app.route('/parameters')
def parameters():
    if 'user_id' not in session:
        return redirect(url_for('connexion'))
    
    user_id = session['user_id']
    user = User.query.get(user_id)
    
    # Get user's projects and associated tasks
    project_tasks = db.session.query(
        Project.project_id,
        Project.name.label('project_name'),
        Task.task_id,
        Task.title,
        Task.status,
        Task.priority,
        Task.end_date
    ).join(Participate, Project.project_id == Participate.project_id)\
     .join(Task, Project.project_id == Task.project_id)\
     .filter(Participate.user_id == user_id)\
     .order_by(Project.name, Task.end_date)\
     .all()
    
    # Organize data by projects for easier templating
    projects_data = {}
    for pt in project_tasks:
        if pt.project_id not in projects_data:
            projects_data[pt.project_id] = {
                'name': pt.project_name,
                'tasks': []
            }
        projects_data[pt.project_id]['tasks'].append({
            'id': pt.task_id,
            'title': pt.title,
            'status': pt.status,
            'priority': pt.priority,
            'end_date': pt.end_date
        })
    
    return render_template('parameters.html', 
                          user=user,
                          projects_data=projects_data)

# Keep the old route as a redirect
@app.route('/user/parameters')
def user_parameters():
    return redirect(url_for('parameters'))

# New route for updating user profile via AJAX
@app.route('/api/update_profile', methods=['POST'])
def update_profile():
    if 'user_id' not in session:
        return {'success': False, 'message': 'Non authentifié'}, 401
    
    user_id = session['user_id']
    user = User.query.get(user_id)
    
    if not user:
        return {'success': False, 'message': 'Utilisateur non trouvé'}, 404
    
    data = request.json
    
    # Update user fields
    if 'name' in data:
        user.name = data['name']
    if 'email' in data:
        # Check if email already exists
        existing_user = User.query.filter_by(email=data['email']).first()
        if existing_user and existing_user.user_id != user_id:
            return {'success': False, 'message': 'Cet email est déjà utilisé'}, 400
        user.email = data['email']
    
    try:
        db.session.commit()
        return {'success': True, 'message': 'Profil mis à jour avec succès'}
    except Exception as e:
        db.session.rollback()
        return {'success': False, 'message': f'Erreur lors de la mise à jour: {str(e)}'}, 500

# Route for updating user password
@app.route('/api/update_password', methods=['POST'])
def update_password():
    if 'user_id' not in session:
        return {'success': False, 'message': 'Non authentifié'}, 401
    
    user_id = session['user_id']
    user = User.query.get(user_id)
    
    if not user:
        return {'success': False, 'message': 'Utilisateur non trouvé'}, 404
    
    data = request.json
    current_password = data.get('currentPassword')
    new_password = data.get('newPassword')
    confirm_password = data.get('confirmPassword')
    
    # Validate inputs
    if not current_password or not new_password or not confirm_password:
        return {'success': False, 'message': 'Tous les champs sont requis'}, 400
    
    if not check_password_hash(user.password, current_password):
        return {'success': False, 'message': 'Mot de passe actuel incorrect'}, 400
    
    if new_password != confirm_password:
        return {'success': False, 'message': 'Les nouveaux mots de passe ne correspondent pas'}, 400
    
    # Update password
    user.password = generate_password_hash(new_password)
    
    try:
        db.session.commit()
        return {'success': True, 'message': 'Mot de passe mis à jour avec succès'}
    except Exception as e:
        db.session.rollback()
        return {'success': False, 'message': f'Erreur lors de la mise à jour: {str(e)}'}, 500

# Route for updating user image
@app.route('/api/update_image', methods=['POST'])
def update_image():
    if 'user_id' not in session:
        return {'success': False, 'message': 'Non authentifié'}, 401
    
    user_id = session['user_id']
    user = User.query.get(user_id)
    
    if not user:
        return {'success': False, 'message': 'Utilisateur non trouvé'}, 404
    
    data = request.json
    image_url = data.get('imageUrl')
    
    # Update user image
    user.image = image_url
    
    try:
        db.session.commit()
        return {'success': True, 'message': 'Image mise à jour avec succès'}
    except Exception as e:
        db.session.rollback()
        return {'success': False, 'message': f'Erreur lors de la mise à jour: {str(e)}'}, 500

# Route for saving user preferences
@app.route('/api/save_preferences', methods=['POST'])
def save_preferences():
    if 'user_id' not in session:
        return {'success': False, 'message': 'Non authentifié'}, 401
    
    # In a real implementation, you would save these preferences to a user_preferences table
    # For now, we'll just acknowledge receipt of the data
    data = request.json
    preference_type = data.get('type')
    
    return {
        'success': True, 
        'message': f'Préférences de {preference_type} enregistrées avec succès',
        'data': data
    }

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)