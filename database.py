# database.py

from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine

# Initialize SQLAlchemy
db = SQLAlchemy()

# Create database engine and session
engine = create_engine('sqlite:///instance/site.db')
Session = sessionmaker(bind=engine)
db_session = Session()

# Define the database models
class User(db.Model, UserMixin):
    """
    User model for authentication.
    Inherits from db.Model and UserMixin for Flask-Login integration.
    """
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(10), nullable=False, default='student') # 'admin', 'teacher', or 'student'
    classroom_id = db.Column(db.Integer, db.ForeignKey('classroom.id'), nullable=True)
    parent_email = db.Column(db.String(120), nullable=True) # Parent's email for notifications
    
    def __repr__(self):
        return f'<User {self.username}>'

class Classroom(db.Model):
    """
    Classroom model for organizing students and teachers.
    """
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(255), nullable=True)
    teacher_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    
    def __repr__(self):
        return f'<Classroom {self.name}>'

# Define relationships after all models are defined to avoid circular dependencies
User.classroom = db.relationship('Classroom', foreign_keys=[User.classroom_id], backref=db.backref('students', lazy=True))
Classroom.teacher = db.relationship('User', foreign_keys=[Classroom.teacher_id], backref=db.backref('teaching_classrooms', lazy=True))

class Attendance(db.Model):
    """
    Attendance record model.
    """
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    classroom_id = db.Column(db.Integer, db.ForeignKey('classroom.id'), nullable=False)
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    status = db.Column(db.String(10), nullable=False) # 'present' or 'absent'
    
    # Relationships
    user = db.relationship('User', backref=db.backref('attendances', lazy=True))
    classroom = db.relationship('Classroom', backref=db.backref('attendances', lazy=True))
    
    def __repr__(self):
        return f'<Attendance {self.user_id} in {self.classroom_id} on {self.date.strftime("%Y-%m-%d")}>'
        
class ClassroomTask(db.Model):
    """
    Task created by teachers for a classroom.
    """
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    classroom_id = db.Column(db.Integer, db.ForeignKey('classroom.id'), nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    due_date = db.Column(db.DateTime, nullable=True)
    
    # Relationships
    classroom = db.relationship('Classroom', backref=db.backref('tasks', lazy=True))
    teacher = db.relationship('User', backref=db.backref('created_tasks', lazy=True))
    
    def __repr__(self):
        return f'<ClassroomTask {self.title} for {self.classroom_id}>'    

class Task(db.Model):
    """
    Task submission model for student responses to classroom tasks.
    """
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    classroom_task_id = db.Column(db.Integer, db.ForeignKey('classroom_task.id'), nullable=True)
    content = db.Column(db.Text, nullable=False)  # Task content/message
    file_path = db.Column(db.String(255), nullable=True)  # Path to uploaded file
    file_type = db.Column(db.String(50), nullable=True)  # Type of file (document, image, etc.)
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref=db.backref('tasks', lazy=True))
    classroom_task = db.relationship('ClassroomTask', backref=db.backref('submissions', lazy=True))
    
    def __repr__(self):
        return f'<Task by {self.user_id}>'