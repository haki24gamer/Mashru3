from flask import Flask, render_template, redirect, url_for, request, session, jsonify, send_file, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import date
from email.message import EmailMessage
from flask_mail import Mail, Message as MailMessage
from flask_socketio import SocketIO, emit, join_room, leave_room
import random
import os
from datetime import datetime, timedelta
import time
try:
    import mysql.connector
except ImportError:
    # MySQL connector not installed
    mysql = None

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

# Initialize SocketIO
socketio = SocketIO(app)

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

# User table
class User(db.Model):
    user_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    image = db.Column(db.String(255))
    password = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DATE, server_default=db.func.current_date())  # Add created_at field

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

# WebSocket event: Join project room
@socketio.on('join_project')
def handle_join_project(data):
    project_id = data.get('project_id')
    if project_id:
        join_room(project_id)
        emit('user_joined', {'message': f'User joined project {project_id}'}, room=project_id)

# WebSocket event: Leave project room
@socketio.on('leave_project')
def handle_leave_project(data):
    project_id = data.get('project_id')
    if project_id:
        leave_room(project_id)
        emit('user_left', {'message': f'User left project {project_id}'}, room=project_id)

# WebSocket event: Send message
@socketio.on('send_message')
def handle_send_message(data):
    project_id = data.get('project_id')
    content = data.get('content', '').strip()
    sender_id = session.get('user_id')

    if not project_id or not content or not sender_id:
        return

    # Save the message to the database
    msg = Message(
        project_id=project_id,
        sender_id=sender_id,
        content=content
    )
    db.session.add(msg)
    db.session.commit()

    # Broadcast the message to the project room
    sender = db.session.get(User, sender_id)
    emit('new_message', {
        'project_id': project_id,  # Include project_id
        'message_id': msg.message_id,
        'sender_id': sender_id,
        'sender_name': sender.name if sender else "Vous",
        'content': msg.content,
        'timestamp': msg.timestamp.strftime('%H:%M')
    }, room=project_id)

@app.route('/get_task_assignees/<int:task_id>')
def get_task_assignees(task_id):
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not authenticated'}), 401
    # Propriétaire
    # Get the task
    task = db.session.get(Task, task_id)
    if not task:
        return jsonify({'success': False, 'message': 'Task not found'}), 404
    
    # Check if user has permission to view this task (must be part of the project)
    user_participation = Participate.query.filter_by(
        user_id=session['user_id'],
        project_id=task.project_id
    ).first()
    
    if not user_participation:
        return jsonify({'success': False, 'message': 'Access denied'}), 403
    
    # Get all users assigned to this task
    assigned_users = db.session.query(Assigned.user_id).filter_by(task_id=task_id).all()
    assignee_ids = [user.user_id for user in assigned_users]
    
    return jsonify({
        'success': True,
        'assignee_ids': assignee_ids
    })

@app.route('/update_task_assignments', methods=['POST'])
def update_task_assignments():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not authenticated'}), 401
    
    data = request.get_json()
    task_id = data.get('task_id')
    user_ids = data.get('user_ids', [])
    
    # Validate data
    if not task_id:
        return jsonify({'success': False, 'message': 'Task ID required'}), 400
    
    # Get the task
    task = db.session.get(Task, task_id)
    if not task:
        return jsonify({'success': False, 'message': 'Task not found'}), 404
    
    # Check if user has permission to modify this task
    current_user_id = session['user_id']
    user_participation = Participate.query.filter_by(
        user_id=current_user_id,
        project_id=task.project_id
    ).first()
    
    if not user_participation:
        return jsonify({'success': False, 'message': 'Access denied to this project'}), 403
    
    is_project_admin = user_participation.role in ['Owner', 'Admin']
    is_assigned_to_task = Assigned.query.filter_by(user_id=current_user_id, task_id=task_id).first()
    
    if not is_project_admin and not is_assigned_to_task:
        return jsonify({'success': False, 'message': 'Permission denied: You must be an admin or assigned to this task to modify assignments'}), 403
    
    try:
        # Remove all current assignments for the task
        Assigned.query.filter_by(task_id=task_id).delete()
        
        # Add new assignments based on the provided list
        for user_id in user_ids:
            # Verify this user is part of the project
            is_project_member = Participate.query.filter_by(
                user_id=user_id,
                project_id=task.project_id
            ).first()
            
            if is_project_member:
                new_assignment = Assigned(
                    user_id=user_id,
                    task_id=task_id
                )
                db.session.add(new_assignment)
            else:
                # Log but continue (skip non-members)
                print(f"Warning: User {user_id} is not a member of this project")
        
        db.session.commit()
        return jsonify({'success': True, 'message': 'Task assignments updated'})
    
    except Exception as e:
        db.session.rollback()
        print(f"Error updating task assignments: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/admin')
def admin_dashboard():
    if 'user_id' not in session:
        return redirect(url_for('connexion'))
    
    # Check if user is an admin
    user = db.session.get(User, session['user_id'])
    if not user or not user.is_admin:
        return redirect(url_for('dashboard'))
    
    # Get statistics for admin dashboard
    total_users = User.query.count()
    total_projects = Project.query.count()
    total_tasks = Task.query.count()
    
    # Handle the case where some users might not have created_at field yet
    try:
        new_users_today = User.query.filter(User.created_at >= date.today()).count()
    except:
        new_users_today = 0  # Fallback if created_at isn't available on some users
    
    # Get recent users
    recent_users = User.query.order_by(User.user_id.desc()).limit(5).all()
    
    # Get projects with most tasks
    project_stats = db.session.query(
        Project.project_id,
        Project.name,
        db.func.count(Task.task_id).label('task_count')
    ).join(Task, Task.project_id == Project.project_id, isouter=True).group_by(
        Project.project_id, Project.name
    ).order_by(db.desc('task_count')).limit(5).all()
    
    return render_template(
        'admin/dashboard.html',
        total_users=total_users,
        total_projects=total_projects,
        total_tasks=total_tasks,
        new_users_today=new_users_today,
        recent_users=recent_users,
        project_stats=project_stats
    )

@app.route('/admin/users')
def admin_users():
    if 'user_id' not in session:
        return redirect(url_for('connexion'))
    
    # Check if user is an admin
    user = db.session.get(User, session['user_id'])
    if not user or not user.is_admin:
        return redirect(url_for('dashboard'))
    
    # Get all users with pagination
    page = request.args.get('page', 1, type=int)
    per_page = 10
    users = User.query.paginate(page=page, per_page=per_page)
    
    return render_template('admin/users.html', users=users)

@app.route('/admin/projects')
def admin_projects():
    if 'user_id' not in session:
        return redirect(url_for('connexion'))
    
    # Check if user is an admin
    user = db.session.get(User, session['user_id'])
    if not user or not user.is_admin:
        return redirect(url_for('dashboard'))
    
    # Get all projects with pagination
    page = request.args.get('page', 1, type=int)
    per_page = 10
    projects = Project.query.paginate(page=page, per_page=per_page)
    
    return render_template('admin/projects.html', projects=projects)

@app.route('/admin/settings')
def admin_settings():
    if 'user_id' not in session:
        return redirect(url_for('connexion'))
    
    # Check if user is an admin
    user = db.session.get(User, session['user_id'])
    if not user or not user.is_admin:
        return redirect(url_for('dashboard'))
    
    return render_template('admin/settings.html')

@app.route('/update_email_config', methods=['POST'])
def update_email_config():
    new_email = request.form.get('emailFrom')
    new_password = request.form.get('emailPassword')
    app.config['MAIL_USERNAME'] = new_email
    app.config['MAIL_PASSWORD'] = new_password
    return redirect(url_for('admin_settings'))

@app.route('/admin/promote_admin', methods=['POST'])
def promote_admin():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not authenticated'}), 401
    
    # Check if current user is an admin
    current_user = db.session.get(User, session['user_id'])
    if not current_user or not current_user.is_admin:
        return jsonify({'success': False, 'message': 'Permission denied'}), 403
    
    data = request.get_json()
    target_user_id = data.get('user_id')
    is_admin = data.get('is_admin', False)
    
    if not target_user_id:
        return jsonify({'success': False, 'message': 'User ID required'}), 400
    
    try:
        target_user = db.session.get(User, target_user_id)
        if not target_user:
            return jsonify({'success': False, 'message': 'User not found'}), 404
        
        target_user.is_admin = is_admin
        db.session.commit()
        
        action = "granted" if is_admin else "revoked"
        return jsonify({
            'success': True,
            'message': f'Admin privileges {action} for {target_user.name}'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/admin/user/<int:user_id>', methods=['GET'])
def admin_user_details(user_id):
    if 'user_id' not in session:
        return redirect(url_for('connexion'))
    
    # Check if user is an admin
    current_user = db.session.get(User, session['user_id'])
    if not current_user or not current_user.is_admin:
        return redirect(url_for('dashboard'))
    
    user = db.session.get(User, user_id)
    
    # Get user's projects
    user_projects = db.session.query(Project).join(Participate).filter(
        Participate.user_id == user_id
    ).all()
    
    # Get user's tasks
    user_tasks = db.session.query(Task).join(Assigned).filter(
        Assigned.user_id == user_id
    ).all()
    
    return render_template('admin/user_details.html', user=user, projects=user_projects, tasks=user_tasks)

@app.route('/admin/delete_user/<int:user_id>', methods=['POST'])
def admin_delete_user(user_id):
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not authenticated'}), 401
    
    # Check if current user is an admin
    current_user = db.session.get(User, session['user_id'])
    if not current_user or not current_user.is_admin:
        return jsonify({'success': False, 'message': 'Permission denied'}), 403
    
    # Prevent self-deletion
    if user_id == session['user_id']:
        return jsonify({'success': False, 'message': 'Cannot delete your own account'}), 400
    
    try:
        user = db.session.get(User, user_id)
        
        # Delete user's task assignments
        Assigned.query.filter_by(user_id=user_id).delete()
        
        # Delete user's project participations
        Participate.query.filter_by(user_id=user_id).delete()
        
        # Delete notifications sent by or to the user
        Notification.query.filter(
            (Notification.sender_id == user_id) | (Notification.recipient_id == user_id)
        ).delete()
        
        # Delete messages sent by the user
        Message.query.filter_by(sender_id=user_id).delete()
        
        # Delete specifications created by the user
        Specification.query.filter_by(created_by=user_id).delete()
        
        # Finally delete the user
        db.session.delete(user)
        db.session.commit()
        
        return jsonify({'success': True, 'message': f'User {user.name} deleted successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/admin/project/<int:project_id>', methods=['GET'])
def admin_project_details(project_id):
    if 'user_id' not in session:
        return redirect(url_for('connexion'))
    
    # Check if user is an admin
    current_user = db.session.get(User, session['user_id'])
    if not current_user or not current_user.is_admin:
        return redirect(url_for('dashboard'))
    
    project = db.session.get(Project, project_id)
    
    # Get project participants
    participants = db.session.query(User, Participate.role).join(
        Participate, User.user_id == Participate.user_id
    ).filter(
        Participate.project_id == project_id
    ).all()
    
    # Get project tasks
    tasks = Task.query.filter_by(project_id=project_id).all()
    
    return render_template(
        'admin/project_details.html',
        project=project,
        participants=participants,
        tasks=tasks
    )

@app.route('/admin/backup_database', methods=['GET'])
def backup_database():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not authenticated'}), 401
    
    # Check if user is an admin
    user = db.session.get(User, session['user_id'])
    if not user or not user.is_admin:
        return jsonify({'success': False, 'message': 'Permission denied'}), 403
    
    try:
        # Path to the current database file
        db_path = os.path.join(app.root_path, 'instance', 'project.db')
        
        # Create a timestamp for the filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Return the database as a downloadable file
        return send_file(
            db_path,
            as_attachment=True,
            download_name=f"mashru3_backup_{timestamp}.db",
            mimetype='application/octet-stream'
        )
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/admin/import_database', methods=['POST'])
def import_database():
    if 'user_id' not in session:
        return redirect(url_for('connexion'))
    
    # Check if user is an admin
    user = db.session.get(User, session['user_id'])
    if not user or not user.is_admin:
        return redirect(url_for('dashboard'))
    
    if 'database_file' not in request.files:
        return redirect(url_for('admin_settings'))
    
    file = request.files['database_file']
    if file.filename == '':
        return redirect(url_for('admin_settings'))
    
    try:
        # Get the current database path
        db_path = os.path.join(app.root_path, 'instance', 'project.db')
        
        # Create a backup before replacing
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = os.path.join(app.root_path, 'instance', f'project_backup_{timestamp}.db')
        
        # Ensure the database connection is closed
        db.session.close()
        
        # Create backup of current database
        if os.path.exists(db_path):
            with open(db_path, 'rb') as current_db:
                with open(backup_path, 'wb') as backup_db:
                    backup_db.write(current_db.read())
        
        # Replace with uploaded file
        file.save(db_path)
        
        # Recreate database connection - use the recommended approach
        db.engine.dispose()
        
        # Flash a success message that will be shown on redirect
        flash('Base de données importée avec succès. Une sauvegarde de l\'ancienne base a été créée.', 'success')
        
        return redirect(url_for('admin_settings'))
    except Exception as e:
        flash(f'Erreur lors de l\'importation de la base de données: {str(e)}', 'error')
        return redirect(url_for('admin_settings'))

@app.route('/update_project/<int:project_id>', methods=['POST'])
def update_project(project_id):
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not authenticated'}), 401
    
    # Get project
    project = db.session.get(Project, project_id)
    if not project:
        return jsonify({'success': False, 'message': 'Project not found'}), 404
    
    # Check if user has permission
    participation = Participate.query.filter_by(
        user_id=session['user_id'],
        project_id=project_id
    ).first()
    
    if not participation or participation.role not in ['Owner', 'Admin']:
        return jsonify({'success': False, 'message': 'You do not have permission to update this project'}), 403
    
    try:
        # Update basic project info
        project.name = request.form.get('name', project.name)
        project.description = request.form.get('description', project.description)
        
        # Update dates
        start_date_str = request.form.get('start_date')
        end_date_str = request.form.get('end_date')
        
        if start_date_str:
            project.start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        if end_date_str:
            project.end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        
        # Handle image upload
        new_image_path = None
        if 'project_image' in request.files:
            file = request.files['project_image']
            if file and file.filename:
                if allowed_file(file.filename):
                    # Create a secure filename with timestamp
                    timestamp = int(time.time())
                    filename = secure_filename(f"project_{timestamp}_{file.filename}")
                    filepath = os.path.join(app.config['PROJECT_IMAGES_FOLDER'], filename)
                    file.save(filepath)
                    
                    # Store the relative path
                    new_image_path = f"/static/uploads/project_images/{filename}"
                    
                    # Remove old image if it exists
                    if project.image:
                        try:
                            old_image_path = os.path.join(app.root_path, project.image.lstrip('/'))
                            if os.path.exists(old_image_path):
                                os.remove(old_image_path)
                        except Exception as e:
                            print(f"Error removing old image: {str(e)}")
                    
                    # Update project with new image
                    project.image = new_image_path
        
        db.session.commit()
        
        response_data = {
            'success': True,
            'message': 'Project updated successfully'
        }
        
        if new_image_path:
            response_data['image_path'] = new_image_path
            
        return jsonify(response_data)
    
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
    
    # Check if the current user is project Owner or Admin
    current_user_participation = Participate.query.filter_by(
        user_id=session['user_id'],
        project_id=project_id
    ).first()
    
    if not current_user_participation or current_user_participation.role not in ['Owner', 'Admin']:
        return jsonify({'success': False, 'message': 'You do not have permission to update roles'}), 403
    
    # If current user is Admin, they can't change Owner's role
    if current_user_participation.role == 'Admin':
        target_participation = Participate.query.filter_by(
            user_id=target_user_id,
            project_id=project_id
        ).first()
        
        if target_participation and target_participation.role == 'Owner':
            return jsonify({'success': False, 'message': 'You cannot change the Chef de projet\'s role'}), 403
    
    try:
        participation = Participate.query.filter_by(
            user_id=target_user_id,
            project_id=project_id
        ).first()
        
        if participation:
            participation.role = new_role
            db.session.commit()
            return jsonify({'success': True, 'message': 'Role updated successfully'})
        else:
            return jsonify({'success': False, 'message': 'User is not a member of this project'}), 404
    
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
    
    # Check if the current user is project Owner or Admin
    current_user_participation = Participate.query.filter_by(
        user_id=session['user_id'],
        project_id=project_id
    ).first()
    
    if not current_user_participation or current_user_participation.role not in ['Owner', 'Admin']:
        return jsonify({'success': False, 'message': 'You do not have permission to remove members'}), 403
    
    # If current user is Admin, they can't remove Owner
    if current_user_participation.role == 'Admin':
        target_participation = Participate.query.filter_by(
            user_id=target_user_id,
            project_id=project_id
        ).first()
        
        if target_participation and target_participation.role == 'Owner':
            return jsonify({'success': False, 'message': 'You cannot remove the Chef de projet of the project'}), 403
    
    # Check if user is trying to remove themselves
    if int(target_user_id) == session['user_id']:
        return jsonify({'success': False, 'message': 'You cannot remove yourself from the project'}), 400
    
    try:
        participation = Participate.query.filter_by(
            user_id=target_user_id,
            project_id=project_id
        ).first()
        
        if participation:
            # Remove user from project
            db.session.delete(participation)
            
            # Also remove user from all tasks in this project
            task_ids = db.session.query(Task.task_id).filter_by(project_id=project_id).all()
            task_ids = [tid[0] for tid in task_ids]
            
            if task_ids:
                Assigned.query.filter(
                    Assigned.user_id == target_user_id,
                    Assigned.task_id.in_(task_ids)
                ).delete(synchronize_session=False)
            
            db.session.commit()
            return jsonify({'success': True, 'message': 'Member removed successfully'})
        else:
            return jsonify({'success': False, 'message': 'User is not a member of this project'}), 404
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/delete_project/<int:project_id>', methods=['POST'])
def delete_project(project_id):
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not authenticated'}), 401
    
    # Check if user has permission (only Owner can delete)
    participation = Participate.query.filter_by(
        user_id=session['user_id'],
        project_id=project_id
    ).first()
    
    if not participation or participation.role != 'Owner':
        return jsonify({'success': False, 'message': 'Only the Chef de projet can delete the project'}), 403
    
    try:
        project = db.session.get(Project, project_id)
        
        if not project:
            return jsonify({'success': False, 'message': 'Project not found'}), 404
        
        # Delete all related records
        
        # 1. Remove tasks assignments
        task_ids = db.session.query(Task.task_id).filter_by(project_id=project_id).all()
        task_ids = [tid[0] for tid in task_ids]
        
        if task_ids:
            Assigned.query.filter(Assigned.task_id.in_(task_ids)).delete(synchronize_session=False)
        
        # 2. Remove tasks
        Task.query.filter_by(project_id=project_id).delete()
        
        # 3. Remove participation records
        Participate.query.filter_by(project_id=project_id).delete()
        
        # 4. Remove notifications related to this project
        Notification.query.filter_by(project_id=project_id).delete()
        
        # 5. Remove specifications
        Specification.query.filter_by(project_id=project_id).delete()
        
        # 6. Remove messages
        Message.query.filter_by(project_id=project_id).delete()
        
        # 7. Delete the project image if it exists
        if project.image:
            try:
                image_path = os.path.join(app.root_path, project.image.lstrip('/'))
                if os.path.exists(image_path):
                    os.remove(image_path)
            except Exception as e:
                print(f"Error removing project image: {str(e)}")
        
        # 8. Finally, delete the project
        db.session.delete(project)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Project deleted successfully'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/add_project', methods=['POST'])
def add_project():
    if 'user_id' not in session:
        return redirect(url_for('connexion'))
    
    user_id = session['user_id']
    name = request.form.get('name')
    description = request.form.get('description')
    start_date_str = request.form.get('start_date')
    end_date_str = request.form.get('end_date')
    
    # Convert string dates to date objects if they're provided
    start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date() if start_date_str else None
    end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date() if end_date_str else None
    
    # Handle image upload
    image_path = None
    if 'image' in request.files:
        file = request.files['image']
        if file and file.filename:
            if allowed_file(file.filename):
                # Create a secure filename with timestamp to avoid conflicts
                timestamp = int(time.time())
                filename = secure_filename(f"project_{timestamp}_{file.filename}")
                filepath = os.path.join(app.config['PROJECT_IMAGES_FOLDER'], filename)
                file.save(filepath)
                # Store the relative path for the database
                image_path = f"/static/uploads/project_images/{filename}"
    
    try:
        # Create new project
        new_project = Project(
            name=name,
            description=description,
            image=image_path,
            start_date=start_date,
            end_date=end_date
        )
        db.session.add(new_project)
        db.session.flush()  # Get the ID of the new project
        
        # Add the current user as the Owner
        participation = Participate(
            user_id=user_id,
            project_id=new_project.project_id,
            role='Owner'
        )
        db.session.add(participation)
        db.session.commit()
        
        flash('Projet créé avec succès!', 'success')
        return redirect(url_for('project_detail', project_id=new_project.project_id))
    
    except Exception as e:
        db.session.rollback()
        print(f"Error creating project: {str(e)}")
        flash(f'Erreur lors de la création du projet: {str(e)}', 'error')
        return redirect(url_for('projects'))

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
            # Pass error message to template
            return render_template('connexion.html', error="Invalid credentials")
    
    # Check for existing_user message from inscription redirect
    existing_user_message = None
    if request.args.get('existing_user'):
        existing_user_message = "Vous avez déjà un compte. Veuillez vous connecter."
        
    return render_template('connexion.html', existing_user_message=existing_user_message)

@app.route('/inscription', methods=['GET', 'POST'])
def inscription():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password_form = request.form['password']

        # Check if user already exists
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            # Redirect to login page with a message
            return redirect(url_for('connexion', existing_user=True))

        password = generate_password_hash(password_form)

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
        user = db.session.get(User, session['user_id'])
        if user:
            return {
                'user_first_name': user.name,
                'user_image': user.image,
                'is_admin': user.is_admin  # Add admin status here
            }
    return {'user_first_name': None, 'user_image': None, 'is_admin': False}

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('connexion'))
    
    user_id = session['user_id']
    user = db.session.get(User, user_id)
    
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
    page = request.args.get('page', 1, type=int)
    search_query = request.args.get('search_query', '')
    per_page = 8 # Number of projects per page

    # Base query for user's projects
    query = db.session.query(Project).join(Participate).filter(Participate.user_id == user_id)

    if search_query:
        query = query.filter(Project.name.ilike(f'%{search_query}%'))
    
    projects_page = query.order_by(Project.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)
    
    # Calculate progress for each project on the current page
    for project in projects_page.items:
        tasks = Task.query.filter_by(project_id=project.project_id).all()
        total_tasks_count = len(tasks)
        
        if total_tasks_count > 0:
            completed_tasks_count = Task.query.filter_by(project_id=project.project_id, status='DONE').count()
            project.progress = round((completed_tasks_count / total_tasks_count) * 100)
        else:
            project.progress = 0
            
    return render_template(
        'project.html', 
        projects_page=projects_page, 
        search_query=search_query
    )

@app.route('/add_task', methods=['POST'])
def add_task():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not authenticated'}), 401
    
    data = request.get_json()
    project_id = data.get('project_id')

    # Permission Check: Only project Chef de projet can add tasks
    participation = Participate.query.filter_by(
        user_id=session['user_id'],
        project_id=project_id
    ).first()

    if not participation or participation.role not in ['Owner', 'Admin']:
        return jsonify({'success': False, 'message': 'Permission denied: Only project chef de projet can create tasks.'}), 403

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
    db.session.commit() # Commit to get task_id

    # Handle task assignments and notifications
    assignee_ids = data.get('assignee_ids', [])
    if assignee_ids:
        project = db.session.get(Project, new_task.project_id)
        assigner = db.session.get(User, session['user_id'])

        for user_id_str in assignee_ids:
            try:
                user_id = int(user_id_str)
                # Check if the user is a member of the project
                is_member = Participate.query.filter_by(
                    user_id=user_id,
                    project_id=new_task.project_id
                ).first()
                
                if is_member:
                    # Check if already assigned (should not happen for new task but good practice)
                    existing_assignment = Assigned.query.filter_by(user_id=user_id, task_id=new_task.task_id).first()
                    if not existing_assignment:
                        assignment = Assigned(
                            user_id=user_id,
                            task_id=new_task.task_id
                        )
                        db.session.add(assignment)

                        # Create notification for the newly assigned user
                        if assigner and project: # Ensure assigner and project details are available
                            notification_content = f"{assigner.name} vous a assigné à la nouvelle tâche '{new_task.title}' dans le projet '{project.name}'."
                            
                            new_notification = Notification(
                                recipient_id=user_id,
                                sender_id=session['user_id'],
                                project_id=new_task.project_id,
                                notification_type='task_assignment',
                                content=notification_content,
                                is_read=False
                            )
                            db.session.add(new_notification)
            except ValueError:
                print(f"Invalid user_id format: {user_id_str}")
                continue # Skip if user_id is not a valid integer
            except Exception as e:
                db.session.rollback() # Rollback on error during assignment/notification
                print(f"Error assigning user {user_id_str} or sending notification: {str(e)}")
                # Optionally, you could return an error response here or collect errors
                # For now, we'll log and continue, then commit successful ones.
        
        try:
            db.session.commit() # Commit all assignments and notifications
        except Exception as e:
            db.session.rollback()
            print(f"Error committing assignments/notifications: {str(e)}")
            return jsonify({'success': False, 'message': 'Erreur lors de l\'assignation des utilisateurs ou de l\'envoi des notifications.'}), 500

    return jsonify({'success': True, 'message': 'Task created successfully', 'task_id': new_task.task_id}), 200

@app.route('/update_task_status', methods=['POST'])
def update_task_status():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not authenticated'}), 401
    
    data = request.get_json()
    task_id = data.get('task_id')
    new_status = data.get('status')
    
    print(f"Updating task {task_id} to status {new_status}")
    
    try:
        task = db.session.get(Task, task_id)
        if not task:
            print(f"Task {task_id} not found")
            return jsonify({'success': False, 'message': 'Task not found'}), 404

        # Permission Check
        current_user_id = session['user_id']
        user_participation = Participate.query.filter_by(
            user_id=current_user_id,
            project_id=task.project_id
        ).first()

        if not user_participation:
            return jsonify({'success': False, 'message': 'Access denied to this project.'}), 403

        is_project_admin = user_participation.role in ['Owner', 'Admin']
        is_assigned_to_task = Assigned.query.filter_by(user_id=current_user_id, task_id=task_id).first()

        if not is_project_admin and not is_assigned_to_task:
            return jsonify({'success': False, 'message': 'Permission denied: You must be a chef de projet or assigned to this task to change its status.'}), 403
            
        # Store the old status for notification message
        old_status = task.status
        
        # Only proceed if the status is actually changing
        if old_status == new_status:
            return jsonify({'success': True, 'message': 'Status unchanged'})
        
        task.status = new_status
        if new_status == 'DONE' and not task.finished_date:
            task.finished_date = date.today()
        elif new_status != 'DONE':
            task.finished_date = None
        
        # Get the user who made the change
        user_who_changed = db.session.get(User, session['user_id'])
        if not user_who_changed:
            print(f"User {session['user_id']} not found")
            return jsonify({'success': False, 'message': 'User not found'}), 404
        
        # Get all users assigned to the task
        assigned_users_query = db.session.query(User).join(
            Assigned, User.user_id == Assigned.user_id
        ).filter(
            Assigned.task_id == task_id,
            User.user_id != session['user_id']  # Don't notify the user who made the change
        )
        
        assigned_users = assigned_users_query.all()
        print(f"Found {len(assigned_users)} assigned users to notify")
        
        # Get project info for the notification
        project = db.session.get(Project, task.project_id)
        if not project:
            print(f"Project {task.project_id} not found")
            # Still continue, just log the error
        
        # Map status codes to more readable French text
        status_map = {
            'TODO': 'À Faire',
            'IN_PROGRESS': 'En cours',
            'REVIEW': 'En révision',
            'DONE': 'Terminé'
        }
        
        notification_count = 0
        # Create notification for each assigned user
        for assigned_user in assigned_users:
            try:
                notification_content = f"{user_who_changed.name} a modifié le statut de la tâche '{task.title}' de '{status_map.get(old_status, old_status)}' à '{status_map.get(new_status, new_status)}' dans le projet '{project.name if project else 'Unknown'}'."
                
                new_notification = Notification(
                    recipient_id=assigned_user.user_id,
                    sender_id=session['user_id'],
                    project_id=task.project_id,
                    notification_type='task_status_change',
                    content=notification_content,
                    is_read=False
                )
                db.session.add(new_notification)
                notification_count += 1
            except Exception as notification_error:
                print(f"Error creating notification for user {assigned_user.user_id}: {str(notification_error)}")
                # Continue with other notifications even if one fails
        
        db.session.commit()
        print(f"Task status updated successfully. Created {notification_count} notifications")
        return jsonify({'success': True, 'message': 'Task status updated successfully'})
    
    except Exception as e:
        db.session.rollback()
        print(f"Error updating task status: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/update_task/<int:task_id>', methods=['POST'])
def update_task(task_id):
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not authenticated'}), 401
    
    data = request.get_json()
    task = db.session.get(Task, task_id)
    
    if task:
        # Permission Check
        current_user_id = session['user_id']
        user_participation = Participate.query.filter_by(
            user_id=current_user_id,
            project_id=task.project_id
        ).first()

        if not user_participation:
            return jsonify({'success': False, 'message': 'Access denied to this project.'}), 403

        is_project_admin = user_participation.role in ['Owner', 'Admin']
        is_assigned_to_task = Assigned.query.filter_by(user_id=current_user_id, task_id=task.task_id).first()

        if not is_project_admin and not is_assigned_to_task:
            return jsonify({'success': False, 'message': 'Permission denied: You must be a chef de projet or assigned to this task to edit it.'}), 403
        
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

@app.route('/delete_task/<int:task_id>', methods=['POST'])
def delete_task(task_id):
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not authenticated'}), 401

    task = db.session.get(Task, task_id)
    if not task:
        return jsonify({'success': False, 'message': 'Task not found'}), 404
    
    # Permission Check
    current_user_id = session['user_id']
    participation = Participate.query.filter_by(
        user_id=current_user_id,
        project_id=task.project_id
    ).first()

    if not participation:
        return jsonify({'success': False, 'message': 'Access denied to this project.'}), 403

    is_project_admin = participation.role in ['Owner', 'Admin']
    is_assigned_to_task = Assigned.query.filter_by(user_id=current_user_id, task_id=task.task_id).first()

    if not is_project_admin and not is_assigned_to_task:
        return jsonify({'success': False, 'message': 'Permission denied: You must be a chef de projet or assigned to this task to delete it.'}), 403

    try:
        # Delete associated assignments first to maintain integrity
        Assigned.query.filter_by(task_id=task_id).delete()
        
        # Delete the task
        db.session.delete(task)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Task deleted successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/project/<int:project_id>')
def project_detail(project_id):
    if 'user_id' not in session:
        return redirect(url_for('connexion'))
    
    current_user_id = session['user_id'] # Get current user's ID
    # Get the current project
    project = db.session.get(Project, project_id)
    
    # Get all project participants with their roles
    participants_data = db.session.query(
        User, Participate.role
    ).join(
        Participate, User.user_id == Participate.user_id
    ).filter(
        Participate.project_id == project_id
    ).all()
    
    # Format participants data for the template
    participants = [{'name': user.name, 'email': user.email, 'user_id': user.user_id, 'role': role, 'profile_picture': user.image} for user, role in participants_data]
    
    # Determine the current user's role in this project
    user_participation = Participate.query.filter_by(
        user_id=session['user_id'],
        project_id=project_id
    ).first()
    
    user_role = user_participation.role if user_participation else None
    is_project_admin = user_role in ['Owner', 'Admin'] if user_role else False
    
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
        is_project_admin=is_project_admin,
        pending_invitations=pending_invites_data,
        current_user_id=current_user_id # Pass current_user_id to template
    )

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
            project = db.session.get(Project, data['project_id'])
            sender = db.session.get(User, session['user_id'])
            
            # Map English role to French for notification message
            role_en = data['role']
            role_fr_map = {
                'Owner': 'Chef de projet',
                'Admin': 'Chef de projet',
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
        notification.sender = db.session.get(User, notification.sender_id)
        if notification.project_id:
            notification.project = db.session.get(Project, notification.project_id)
    
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
    
    notification = db.session.get(Notification, notification_id)
    
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
                'Chef de projet': 'Owner',
                'Chef de projet': 'Admin',
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
    
    notification = db.session.get(Notification, notification_id)
    
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

@app.route('/get_task/<int:task_id>')
def get_task(task_id):
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not authenticated'}), 401
    
    task = db.session.get(Task, task_id)
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

@app.route('/parametre', methods=['GET', 'POST'])
def parametre():
    if 'user_id' not in session:
        return redirect(url_for('connexion'))
    
    user_id = session['user_id']
    user = db.session.get(User, user_id)
    success_message = None
    error_message = None
    email_change_pending = False
    pending_email = None
    
    if request.method == 'POST':
        action = request.form.get('action', '')
        
        if action == 'update_info':
            # Store old image path before any changes
            old_image_path = user.image

            # Update basic info
            user.name = request.form.get('name', user.name)
            
            # Check if email is being changed and if it's not already taken
            new_email = request.form.get('email')
            if new_email and new_email != user.email:
                # check uniqueness
                if User.query.filter_by(email=new_email).first():
                    error_message = "Cet e-mail est déjà utilisé par un autre compte."
                else:
                    # generate token & store pending change
                    token = ''.join(random.choices('0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ', k=32))
                    session['email_change'] = {
                        'new_email': new_email,
                        'token': token,
                        'expiry': (datetime.now() + timedelta(hours=1)).timestamp()
                    }
                    # send verification email
                    confirm_link = url_for('confirm_email_change', token=token, _external=True)
                    msg = MailMessage(
                        'Confirmez votre nouvelle adresse email',
                        sender=app.config['MAIL_USERNAME'],
                        recipients=[new_email]
                    )
                    msg.body = f"Bonjour {user.name},\n\nCliquez sur ce lien pour confirmer votre nouvelle adresse email :\n{confirm_link}\n\nCe lien expire dans 1 heure."
                    try:
                        mail.send(msg)
                        success_message = "Un email de vérification a été envoyé à votre nouvelle adresse."
                        email_change_pending = True
                        pending_email = new_email
                    except Exception as e:
                        error_message = "Impossible d'envoyer l'email de confirmation. Veuillez réessayer."
            
            # Handle profile picture upload
            if 'profile_picture' in request.files:
                file = request.files['profile_picture']
                if file and file.filename:
                    if allowed_file(file.filename):
                        try:
                            # Create a secure filename and save the file
                            timestamp = int(time.time()) # Add timestamp for uniqueness
                            filename = secure_filename(f"user_{user_id}_{timestamp}_{file.filename}")
                            filepath = os.path.join(app.config['PROFILE_PICS_FOLDER'], filename)
                            file.save(filepath)
                            
                            # Update the user's profile image path in the database
                            relative_path = f"/static/uploads/profile_pics/{filename}"
                            user.image = relative_path

                            # Delete the old profile picture if it exists and is different
                            if old_image_path and old_image_path != user.image:
                                try:
                                    # Construct the absolute path for the old image
                                    old_image_full_path = os.path.join(app.root_path, old_image_path.lstrip('/'))
                                    if os.path.exists(old_image_full_path):
                                        os.remove(old_image_full_path)
                                        print(f"Deleted old profile picture: {old_image_full_path}") # Optional: for logging
                                except Exception as e_delete:
                                    print(f"Error deleting old profile picture {old_image_path}: {str(e_delete)}") # Log error but continue
                        except Exception as e:
                            error_message = f"Erreur lors du téléchargement de l'image: {str(e)}"
                    else:
                        error_message = "Format d'image non supporté. Utilisez JPG, PNG ou GIF."
            
            if not error_message and not email_change_pending: # Only commit if no email change is pending or if it's just name/pic update
                db.session.commit()
                success_message = "Vos informations ont été mises à jour avec succès."
            elif not error_message and email_change_pending:
                # If email change is pending, we still commit name changes if any.
                # The email itself is not committed here.
                db.session.commit() 
                # The success_message for email verification is already set.
        
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
    
    # Show confirmation banner if link clicked
    email_confirmed = request.args.get('email_confirmed') == '1'
    return render_template(
        'parametre.html',
        user=user,
        success_message=success_message,
        error_message=error_message,
        email_change_pending=email_change_pending,
        pending_email=pending_email,
        email_confirmed=email_confirmed
    )

@app.route('/confirm_email/<token>')
def confirm_email_change(token):
    if 'user_id' not in session or 'email_change' not in session:
        return redirect(url_for('parametre'))
    data = session['email_change']
    # validate token & expiry
    if data.get('token') != token or data.get('expiry', 0) < datetime.now().timestamp():
        return redirect(url_for('parametre'))
    user = db.session.get(User, session['user_id'])
    if user:
        user.email = data['new_email']
        db.session.commit()
    session.pop('email_change', None)
    return redirect(url_for('parametre', email_confirmed=1))

@app.route('/deconnexion', methods=['GET', 'POST'])
def deconnexion():
    # ...existing code...
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
        sender = db.session.get(User, msg.sender_id)
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
    sender = db.session.get(User, session['user_id'])
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
            project = db.session.get(Project, spec.project_id)
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

@app.route('/specification/<int:specification_id>')
def view_specification(specification_id):
    if 'user_id' not in session:
        return redirect(url_for('connexion'))
    
    specification = db.session.get(Specification, specification_id)
    
    # Check if user has access to the project
    participation = Participate.query.filter_by(
        user_id=session['user_id'],
        project_id=specification.project_id
    ).first()
    
    if not participation:
        return "Vous n'avez pas accès à ce cahier des charges", 403
    
    # Get project info
    project = db.session.get(Project, specification.project_id)
    
    return render_template('view_specification.html', 
                          specification=specification, 
                          project=project)

@app.route('/edit_specification/<int:specification_id>')
def edit_specification(specification_id):
    if 'user_id' not in session:
        return redirect(url_for('connexion'))
    
    specification = db.session.get(Specification, specification_id)
    
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
    project = db.session.get(Project, specification.project_id)
    
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
    
    specification = db.session.get(Specification, specification_id)
    
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
    
    specification = db.session.get(Specification, specification_id)
    
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
    socketio.run(app, debug=True, port=port, host="0.0.0.0")
