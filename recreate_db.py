from app import app, db, User
from werkzeug.security import generate_password_hash

with app.app_context():
    # Drop all tables and recreate them
    db.drop_all()
    db.create_all()
    
    # Create an admin user
    admin = User(
        name="Admin User",
        email="admin@example.com",
        password=generate_password_hash("secure_password"),
        is_admin=True
    )
    
    db.session.add(admin)
    db.session.commit()
    
    print("Database recreated with admin user")
    print("Admin email: admin@example.com")
    print("Admin password: secure_password")
