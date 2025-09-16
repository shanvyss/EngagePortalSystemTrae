# recreate_db.py

import os
import sqlite3
from flask import Flask
from database import db, User, Classroom, Attendance, ClassroomTask, Task
from flask_bcrypt import Bcrypt

# Remove existing database
db_path = 'instance/site.db'
if os.path.exists(db_path):
    print(f"Removing existing database at {db_path}")
    os.remove(db_path)

# Create directory if it doesn't exist
instance_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance')
os.makedirs(instance_dir, exist_ok=True)
print(f"Created instance directory at {instance_dir}")

# Create a Flask app and initialize the database
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

# Initialize Bcrypt
bcrypt = Bcrypt(app)

# Create application context
with app.app_context():
    # Create all tables
    print("Creating database tables...")
    db.create_all()

    # Create default admin user
    print("Creating default admin user...")
    admin = User(username='admin', password_hash=bcrypt.generate_password_hash('admin').decode('utf-8'), role='admin')
    db.session.add(admin)

    # Create default classroom
    print("Creating default classroom...")
    classroom = Classroom(name='Default Classroom', description='Default classroom for all students')
    db.session.add(classroom)

    # Create test teacher
    print("Creating test teacher...")
    teacher = User(username='test_teacher', password_hash=bcrypt.generate_password_hash('password').decode('utf-8'), role='teacher')
    db.session.add(teacher)

    # Create test student
    print("Creating test student...")
    student = User(
        username='student1', 
        password_hash=bcrypt.generate_password_hash('password').decode('utf-8'), 
        role='student',
        parent_email='parent@example.com'
    )
    db.session.add(student)

    # Commit changes
    db.session.commit()

    # Assign teacher to classroom
    classroom.teacher_id = teacher.id
    teacher.classroom_id = classroom.id

    # Assign student to classroom
    student.classroom_id = classroom.id

    # Commit changes
    db.session.commit()

print("Database recreated successfully!")