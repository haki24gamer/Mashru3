import os
from app import app, db, User
from werkzeug.security import generate_password_hash

# THIS WILL DELETE YOUR DATABASE! Only use in development
# Back up your data before running this

with app.app_context():
    # Delete the database file
    db_path = 'project.db'  # Path relative to where app.py is executed
    if os.path.exists(db_path):
        # For safety, confirm action
        print("⚠️ WARNING: This will delete your database and all data!")
        confirm = input("Type 'YES' to confirm: ")
        if confirm == "YES":
            db.drop_all()
            print("Database tables dropped.")
            
            # Create all tables fresh
            db.create_all()
            print("Database tables recreated.")
            
            # Create admin user
            admin_name = input("Enter admin name: ")
            admin_email = input("Enter admin email: ")
            admin_password = input("Enter admin password: ")
            
            admin = User(
                name=admin_name,
                email=admin_email,
                password=generate_password_hash(admin_password),
                is_admin=True
            )
            
            db.session.add(admin)
            db.session.commit()
            
            print(f"Admin user created! Email: {admin_email}")
        else:
            print("Operation cancelled.")
    else:
        print("Database file not found.")
