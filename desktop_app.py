# desktop_app.py

import sys
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QPushButton, QLabel, QLineEdit, QComboBox, QTableWidget,
                             QTableWidgetItem, QMessageBox, QTabWidget, QFormLayout,
                             QTextEdit, QGroupBox, QStackedWidget, QDialog, QDialogButtonBox,
                             QFileDialog, QCheckBox, QProgressDialog, QListWidget, QListWidgetItem)
from PyQt5.QtCore import Qt, pyqtSignal, QDate
from PyQt5.QtGui import QFont, QColor
from flask_bcrypt import Bcrypt
from datetime import datetime, date

# Import the dialog classes
from create_classroom_task_dialog import CreateClassroomTaskDialog
from task_submissions_dialog import TaskSubmissionsDialog
from submit_task_dialog import SubmitTaskDialog

# Import database models
from database import db, User, Classroom, Attendance, Task, ClassroomTask, ClassroomMembership

# Initialize SQLAlchemy and Bcrypt
bcrypt = Bcrypt()

# For file uploads
import os
import time
import shutil
from werkzeug.utils import secure_filename

# Create uploads directory if it doesn't exist
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'doc', 'docx'}
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Helper functions
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Configure SQLAlchemy
import sqlalchemy
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Create database engine and session
engine = create_engine('sqlite:///instance/site.db')
Session = sessionmaker(bind=engine)
db_session = Session()

# Login Window
class LoginWindow(QWidget):
    login_successful = pyqtSignal(User)
    
    def __init__(self):
        super().__init__()
        self.init_ui()
        
    def init_ui(self):
        self.setWindowTitle('Login')
        self.setGeometry(300, 300, 400, 200)
        
        # Create layout
        layout = QVBoxLayout()
        
        # Create form layout
        form_layout = QFormLayout()
        
        # Username field
        self.username_input = QLineEdit()
        form_layout.addRow('Username:', self.username_input)
        
        # Password field
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        form_layout.addRow('Password:', self.password_input)
        
        # Add form to main layout
        layout.addLayout(form_layout)
        
        # Login button
        self.login_button = QPushButton('Login')
        self.login_button.clicked.connect(self.login)
        layout.addWidget(self.login_button)
        
        # Error message label
        self.error_label = QLabel('')
        self.error_label.setStyleSheet('color: red')
        layout.addWidget(self.error_label)
        
        self.setLayout(layout)
        
    def login(self):
        username = self.username_input.text()
        password = self.password_input.text()
        
        # Find user in database
        user = db_session.query(User).filter_by(username=username).first()
        
        if user and bcrypt.check_password_hash(user.password_hash, password):
            self.login_successful.emit(user)
        else:
            self.error_label.setText('Invalid username or password')

# Admin Dashboard
class AdminDashboard(QWidget):
    def __init__(self, user):
        super().__init__()
        self.user = user
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Header
        header_layout = QHBoxLayout()
        welcome_label = QLabel(f'Welcome, {self.user.username}!')
        welcome_label.setFont(QFont('Arial', 14, QFont.Bold))
        header_layout.addWidget(welcome_label)
        
        # Logout button
        logout_button = QPushButton('Logout')
        logout_button.clicked.connect(self.logout)
        header_layout.addWidget(logout_button)
        layout.addLayout(header_layout)
        
        # Tabs for different sections
        tabs = QTabWidget()
        
        # Classrooms tab
        classrooms_tab = QWidget()
        classrooms_layout = QVBoxLayout(classrooms_tab)
        
        # Create classroom button
        create_classroom_button = QPushButton('Create New Classroom')
        create_classroom_button.clicked.connect(self.show_create_classroom_dialog)
        classrooms_layout.addWidget(create_classroom_button)
        
        # Classrooms table
        self.classrooms_table = QTableWidget()
        self.classrooms_table.setColumnCount(3)
        self.classrooms_table.setHorizontalHeaderLabels(['Name', 'Teacher', 'Actions'])
        self.load_classrooms()
        classrooms_layout.addWidget(self.classrooms_table)
        
        # Users tab
        users_tab = QWidget()
        users_layout = QVBoxLayout(users_tab)
        
        # Create user button
        create_user_button = QPushButton('Create New User')
        create_user_button.clicked.connect(self.show_create_user_dialog)
        users_layout.addWidget(create_user_button)
        
        # Users table
        self.users_table = QTableWidget()
        self.users_table.setColumnCount(4)
        self.users_table.setHorizontalHeaderLabels(['Username', 'Role', 'Classroom', 'Actions'])
        self.load_users()
        users_layout.addWidget(self.users_table)
        
        # Add tabs to tab widget
        tabs.addTab(classrooms_tab, 'Classrooms')
        tabs.addTab(users_tab, 'Users')
        
        layout.addWidget(tabs)
        self.setLayout(layout)
        
    def load_classrooms(self):
        classrooms = db_session.query(Classroom).all()
        self.classrooms_table.setRowCount(len(classrooms))
        
        for row, classroom in enumerate(classrooms):
            # Name
            name_item = QTableWidgetItem(classroom.name)
            self.classrooms_table.setItem(row, 0, name_item)
            
            # Teacher
            teacher_name = classroom.teacher.username if classroom.teacher else 'No teacher assigned'
            teacher_item = QTableWidgetItem(teacher_name)
            self.classrooms_table.setItem(row, 1, teacher_item)
            
            # Actions
            view_button = QPushButton('View Details')
            view_button.clicked.connect(lambda _, c_id=classroom.id: self.view_classroom_details(c_id))
            self.classrooms_table.setCellWidget(row, 2, view_button)
        
        self.classrooms_table.resizeColumnsToContents()
    
    def load_users(self):
        users = db_session.query(User).filter(User.role.in_(['student', 'teacher'])).all()
        self.users_table.setRowCount(len(users))
        
        for row, user in enumerate(users):
            # Username
            username_item = QTableWidgetItem(user.username)
            self.users_table.setItem(row, 0, username_item)
            
            # Role
            role_item = QTableWidgetItem(user.role)
            self.users_table.setItem(row, 1, role_item)
            
            # Classroom
            classroom_name = user.classroom.name if user.classroom else 'Not assigned'
            classroom_item = QTableWidgetItem(classroom_name)
            self.users_table.setItem(row, 2, classroom_item)
            
            # Actions
            assign_button = QPushButton('Assign Classroom')
            assign_button.clicked.connect(lambda _, u_id=user.id: self.show_assign_classroom_dialog(u_id))
            self.users_table.setCellWidget(row, 3, assign_button)
        
        self.users_table.resizeColumnsToContents()
    
    def show_create_classroom_dialog(self):
        dialog = CreateClassroomDialog()
        if dialog.exec_() == QDialog.Accepted:
            self.load_classrooms()
    
    def show_create_user_dialog(self):
        dialog = CreateUserDialog()
        if dialog.exec_() == QDialog.Accepted:
            self.load_users()
    
    def show_assign_classroom_dialog(self, user_id):
        dialog = AssignClassroomDialog(user_id)
        if dialog.exec_() == QDialog.Accepted:
            self.load_users()
    
    def view_classroom_details(self, classroom_id):
        dialog = ClassroomDetailsDialog(classroom_id, self.user)
        dialog.exec_()
    
    def logout(self):
        # Clear session
        from session import clear
        clear()
        self.parent().show_login()

# Teacher Dashboard
class TeacherDashboard(QWidget):
    def __init__(self, user):
        super().__init__()
        self.user = user
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Header
        header_layout = QHBoxLayout()
        welcome_label = QLabel(f'Welcome, {self.user.username}!')
        welcome_label.setFont(QFont('Arial', 14, QFont.Bold))
        header_layout.addWidget(welcome_label)
        
        # Logout button
        logout_button = QPushButton('Logout')
        logout_button.clicked.connect(self.logout)
        header_layout.addWidget(logout_button)
        layout.addLayout(header_layout)
        
        # Classrooms section
        classrooms_group = QGroupBox('Your Classrooms')
        classrooms_layout = QVBoxLayout()
        
        # Classrooms table
        self.classrooms_table = QTableWidget()
        self.classrooms_table.setColumnCount(2)
        self.classrooms_table.setHorizontalHeaderLabels(['Name', 'Actions'])
        self.load_classrooms()
        classrooms_layout.addWidget(self.classrooms_table)
        
        classrooms_group.setLayout(classrooms_layout)
        layout.addWidget(classrooms_group)
        
        self.setLayout(layout)
        
    def load_classrooms(self):
        classrooms = db_session.query(Classroom).filter_by(teacher_id=self.user.id).all()
        self.classrooms_table.setRowCount(len(classrooms))
        
        for row, classroom in enumerate(classrooms):
            # Name
            name_item = QTableWidgetItem(classroom.name)
            self.classrooms_table.setItem(row, 0, name_item)
            
            # Actions
            view_button = QPushButton('View Details')
            view_button.clicked.connect(lambda _, c_id=classroom.id: self.view_classroom_details(c_id))
            self.classrooms_table.setCellWidget(row, 1, view_button)
        
        self.classrooms_table.resizeColumnsToContents()
    
    def view_classroom_details(self, classroom_id):
        dialog = ClassroomDetailsDialog(classroom_id, self.user)
        dialog.exec_()
    
    def logout(self):
        # Clear session
        from session import clear
        clear()
        self.parent().show_login()

# Student Dashboard
class StudentDashboard(QWidget):
    def __init__(self, user):
        super().__init__()
        self.user = user
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Header
        header_layout = QHBoxLayout()
        welcome_label = QLabel(f'Welcome, {self.user.username}!')
        welcome_label.setFont(QFont('Arial', 14, QFont.Bold))
        header_layout.addWidget(welcome_label)
        
        # Logout button
        logout_button = QPushButton('Logout')
        logout_button.clicked.connect(self.logout)
        header_layout.addWidget(logout_button)
        layout.addLayout(header_layout)
        
        # Classroom info
        classroom_group = QGroupBox('Your Classroom')
        classroom_layout = QVBoxLayout()
        
        if self.user.classroom:
            classroom_name = QLabel(f'Name: {self.user.classroom.name}')
            classroom_layout.addWidget(classroom_name)
            
            if self.user.classroom.teacher:
                teacher_name = QLabel(f'Teacher: {self.user.classroom.teacher.username}')
                classroom_layout.addWidget(teacher_name)
        else:
            not_assigned = QLabel('You are not assigned to any classroom')
            classroom_layout.addWidget(not_assigned)
        
        classroom_group.setLayout(classroom_layout)
        layout.addWidget(classroom_group)
        
        # Tasks section
        tasks_group = QGroupBox('Your Tasks')
        tasks_layout = QVBoxLayout()
        
        # Submit task form
        form_layout = QFormLayout()
        self.task_content = QTextEdit()
        form_layout.addRow('Task Content:', self.task_content)
        
        submit_button = QPushButton('Submit Task')
        submit_button.clicked.connect(self.submit_task)
        form_layout.addRow('', submit_button)
        
        tasks_layout.addLayout(form_layout)
        
        # Tasks table
        self.tasks_table = QTableWidget()
        self.tasks_table.setColumnCount(2)
        self.tasks_table.setHorizontalHeaderLabels(['Content', 'Date'])
        self.load_tasks()
        tasks_layout.addWidget(self.tasks_table)
        
        tasks_group.setLayout(tasks_layout)
        layout.addWidget(tasks_group)
        
        self.setLayout(layout)
        
    def load_tasks(self):
        tasks = db_session.query(Task).filter_by(user_id=self.user.id).all()
        self.tasks_table.setRowCount(len(tasks))
        
        for row, task in enumerate(tasks):
            # Content
            content_item = QTableWidgetItem(task.content)
            self.tasks_table.setItem(row, 0, content_item)
            
            # Date
            date_item = QTableWidgetItem(task.date.strftime('%Y-%m-%d %H:%M'))
            self.tasks_table.setItem(row, 1, date_item)
        
        self.tasks_table.resizeColumnsToContents()
    
    def submit_task(self):
        content = self.task_content.toPlainText()
        
        if not content:
            QMessageBox.warning(self, 'Error', 'Task content cannot be empty')
            return
        
        new_task = Task(user_id=self.user.id, content=content)
        db_session.add(new_task)
        db_session.commit()
        
        QMessageBox.information(self, 'Success', 'Task submitted successfully')
        self.task_content.clear()
        self.load_tasks()
    
    def logout(self):
        # Clear session
        from session import clear
        clear()
        self.parent().show_login()

# Create Classroom Dialog
class CreateClassroomDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.init_ui()
        
    def init_ui(self):
        self.setWindowTitle('Create Classroom')
        self.setGeometry(300, 300, 400, 200)
        
        layout = QVBoxLayout()
        
        # Form layout
        form_layout = QFormLayout()
        
        # Name field
        self.name_input = QLineEdit()
        form_layout.addRow('Name:', self.name_input)
        
        # Description field
        self.description_input = QTextEdit()
        form_layout.addRow('Description:', self.description_input)
        
        # Teacher dropdown
        self.teacher_combo = QComboBox()
        self.teacher_combo.addItem('No teacher', None)
        
        teachers = db_session.query(User).filter_by(role='teacher').all()
        for teacher in teachers:
            self.teacher_combo.addItem(teacher.username, teacher.id)
        
        form_layout.addRow('Teacher:', self.teacher_combo)
        
        layout.addLayout(form_layout)
        
        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.create_classroom)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
        self.setLayout(layout)
        
    def create_classroom(self):
        name = self.name_input.text()
        description = self.description_input.toPlainText()
        teacher_id = self.teacher_combo.currentData()
        
        if not name:
            QMessageBox.warning(self, 'Error', 'Classroom name is required')
            return
        
        new_classroom = Classroom(name=name, description=description)
        
        if teacher_id:
            new_classroom.teacher_id = teacher_id
        
        db_session.add(new_classroom)
        db_session.commit()
        
        QMessageBox.information(self, 'Success', f'Classroom "{name}" created successfully')
        self.accept()

# Create User Dialog
class CreateUserDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.init_ui()
        
    def init_ui(self):
        self.setWindowTitle('Create User')
        self.setGeometry(300, 300, 400, 300)
        
        layout = QVBoxLayout()
        
        # Form layout
        form_layout = QFormLayout()
        
        # Username field
        self.username_input = QLineEdit()
        form_layout.addRow('Username:', self.username_input)
        
        # Password field
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        form_layout.addRow('Password:', self.password_input)
        
        # Role dropdown
        self.role_combo = QComboBox()
        self.role_combo.addItem('Student', 'student')
        self.role_combo.addItem('Teacher', 'teacher')
        self.role_combo.currentIndexChanged.connect(self.on_role_changed)
        form_layout.addRow('Role:', self.role_combo)
        
        # Parent email field (initially hidden, only for students)
        self.parent_email_input = QLineEdit()
        self.parent_email_label = QLabel('Parent Email:')
        form_layout.addRow(self.parent_email_label, self.parent_email_input)
        
        # Initially hide parent email field
        self.parent_email_label.setVisible(True)
        self.parent_email_input.setVisible(True)
        
        # Classroom dropdown
        self.classroom_combo = QComboBox()
        self.classroom_combo.addItem('No classroom', None)
        
        classrooms = db_session.query(Classroom).all()
        for classroom in classrooms:
            self.classroom_combo.addItem(classroom.name, classroom.id)
        
        form_layout.addRow('Classroom:', self.classroom_combo)
        
        layout.addLayout(form_layout)
        
        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.create_user)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
        self.setLayout(layout)
        
        # Set initial visibility based on default role
        self.on_role_changed(0)
        
    def on_role_changed(self, index):
        # Show parent email field only for students
        role = self.role_combo.currentData()
        is_student = (role == 'student')
        self.parent_email_label.setVisible(is_student)
        self.parent_email_input.setVisible(is_student)
    
    def create_user(self):
        username = self.username_input.text()
        password = self.password_input.text()
        role = self.role_combo.currentData()
        classroom_id = self.classroom_combo.currentData()
        parent_email = self.parent_email_input.text() if role == 'student' else None
        
        if not username or not password:
            QMessageBox.warning(self, 'Error', 'Username and password are required')
            return
        
        # Check if username already exists
        existing_user = db_session.query(User).filter_by(username=username).first()
        if existing_user:
            QMessageBox.warning(self, 'Error', f'Username {username} already exists')
            return
        
        # Validate parent email format if provided
        if parent_email and '@' not in parent_email:
            QMessageBox.warning(self, 'Error', 'Please enter a valid parent email address')
            return
        
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        
        new_user = User(username=username, password_hash=hashed_password, role=role, parent_email=parent_email)
        db_session.add(new_user)
        db_session.commit()  # ensure new_user.id is available

        if classroom_id:
            new_user.classroom_id = classroom_id
            
            # If role is teacher, also set as classroom teacher
            if role == 'teacher':
                classroom = db_session.query(Classroom).get(classroom_id)
                if classroom:
                    classroom.teacher_id = new_user.id
            else:
                # Add many-to-many membership for students
                if not db_session.query(ClassroomMembership).filter_by(user_id=new_user.id, classroom_id=classroom_id).first():
                    db_session.add(ClassroomMembership(user_id=new_user.id, classroom_id=classroom_id))
        
        db_session.commit()
        
        QMessageBox.information(self, 'Success', f'User {username} created successfully')
        self.accept()

# Assign Classroom Dialog
class AssignClassroomDialog(QDialog):
    def __init__(self, user_id):
        super().__init__()
        self.user_id = user_id
        self.user = db_session.query(User).get(user_id)
        self.init_ui()
        
    def init_ui(self):
        self.setWindowTitle('Assign Classrooms')
        self.setGeometry(300, 300, 500, 420)
        
        layout = QVBoxLayout()
        
        # User info
        user_info = QLabel(f'Assigning classrooms for: {self.user.username} ({self.user.role})')
        layout.addWidget(user_info)
        
        # Form layout
        form_layout = QFormLayout()
        
        # Multi-select list of classrooms
        self.class_list = QListWidget()
        self.class_list.setSelectionMode(QListWidget.MultiSelection)
        classrooms = db_session.query(Classroom).all()
        current_ids = set()
        if self.user.classroom_id:
            current_ids.add(self.user.classroom_id)
        for m in db_session.query(ClassroomMembership).filter_by(user_id=self.user.id).all():
            current_ids.add(m.classroom_id)
        for classroom in classrooms:
            item = QListWidgetItem(classroom.name)
            item.setData(Qt.UserRole, classroom.id)
            self.class_list.addItem(item)
            if classroom.id in current_ids:
                item.setSelected(True)
        form_layout.addRow('Classrooms:', self.class_list)
        
        layout.addLayout(form_layout)
        
        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.assign_classroom)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
        self.setLayout(layout)
        
    def assign_classroom(self):
        selected_ids = [self.class_list.item(i).data(Qt.UserRole) for i in range(self.class_list.count()) if self.class_list.item(i).isSelected()]
        
        # Primary/legacy classroom is first selected (if any)
        self.user.classroom_id = selected_ids[0] if selected_ids else None
        
        # Teachers: set as teacher in selected classrooms
        if self.user.role == 'teacher':
            for cid in selected_ids:
                classroom = db_session.query(Classroom).get(cid)
                if classroom:
                    classroom.teacher_id = self.user.id
        
        # Sync memberships
        existing = {m.classroom_id: m for m in db_session.query(ClassroomMembership).filter_by(user_id=self.user.id).all()}
        for cid, membership in list(existing.items()):
            if cid not in selected_ids:
                db_session.delete(membership)
        for cid in selected_ids:
            if cid not in existing:
                db_session.add(ClassroomMembership(user_id=self.user.id, classroom_id=cid))
        
        db_session.commit()
        
        QMessageBox.information(self, 'Success', f'Classrooms updated for {self.user.username}')
        self.accept()

# Classroom Details Dialog
class ClassroomDetailsDialog(QDialog):
    def __init__(self, classroom_id, current_user):
        super().__init__()
        self.classroom_id = classroom_id
        self.classroom = db_session.query(Classroom).get(classroom_id)
        self.current_user = current_user
        self.init_ui()
        
    def init_ui(self):
        self.setWindowTitle(f'Classroom: {self.classroom.name}')
        self.setGeometry(300, 300, 800, 600)
        
        layout = QVBoxLayout()
        
        # Classroom info
        info_layout = QFormLayout()
        info_layout.addRow('Name:', QLabel(self.classroom.name))
        info_layout.addRow('Description:', QLabel(self.classroom.description or 'No description'))
        
        teacher_name = self.classroom.teacher.username if self.classroom.teacher else 'No teacher assigned'
        info_layout.addRow('Teacher:', QLabel(teacher_name))
        
        layout.addLayout(info_layout)
        
        # Tasks section for teachers and admins
        if self.current_user.role in ['teacher', 'admin']:
            tasks_group = QGroupBox('Classroom Tasks')
            tasks_layout = QVBoxLayout()
            
            # Create task button
            create_task_btn = QPushButton('Create New Task')
            create_task_btn.clicked.connect(self.create_task)
            tasks_layout.addWidget(create_task_btn)
            
            # Tasks table
            self.tasks_table = QTableWidget()
            self.tasks_table.setColumnCount(5)
            self.tasks_table.setHorizontalHeaderLabels(['Title', 'Description', 'Due Date', 'Created', 'Actions'])
            self.load_tasks()
            tasks_layout.addWidget(self.tasks_table)
            
            tasks_group.setLayout(tasks_layout)
            layout.addWidget(tasks_group)
        
        # Tasks section for students
        if self.current_user.role == 'student':
            tasks_group = QGroupBox('Classroom Tasks')
            tasks_layout = QVBoxLayout()
            
            # Tasks table
            self.tasks_table = QTableWidget()
            self.tasks_table.setColumnCount(5)
            self.tasks_table.setHorizontalHeaderLabels(['Title', 'Description', 'Due Date', 'Status', 'Actions'])
            self.load_student_tasks()
            tasks_layout.addWidget(self.tasks_table)
            
            tasks_group.setLayout(tasks_layout)
            layout.addWidget(tasks_group)
        
        # Students section
        students_group = QGroupBox('Students')
        students_layout = QVBoxLayout()
        
        # Students table
        self.students_table = QTableWidget()
        self.students_table.setColumnCount(4)
        self.students_table.setHorizontalHeaderLabels(['Username', 'Attendance', 'Email', 'Actions'])
        # Make sure the table is not editable
        self.students_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.load_students()
        students_layout.addWidget(self.students_table)
        
        students_group.setLayout(students_layout)
        layout.addWidget(students_group)
        
        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.Close)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
        self.setLayout(layout)
        
    def load_students(self):
        # Students via legacy classroom_id or membership
        legacy = db_session.query(User).filter_by(classroom_id=self.classroom_id, role='student')
        member = db_session.query(User).join(ClassroomMembership, ClassroomMembership.user_id == User.id) \
            .filter(ClassroomMembership.classroom_id == self.classroom_id, User.role == 'student')
        students = legacy.union(member).all()
        self.students_table.setRowCount(len(students))
        
        # Get today's attendance records
        today = date.today()
        attendance_records = db_session.query(Attendance).filter(
            Attendance.classroom_id == self.classroom_id,
            Attendance.date >= today
        ).all()
        
        # Create a dictionary of user_id -> attendance status for easy lookup
        attendance_dict = {record.user_id: record.status for record in attendance_records}
        
        for row, student in enumerate(students):
            # Username
            username_item = QTableWidgetItem(student.username)
            self.students_table.setItem(row, 0, username_item)
            
            # Attendance status
            status = attendance_dict.get(student.id, 'Not marked')
            status_item = QTableWidgetItem(status)
            
            if status == 'present':
                status_item.setBackground(QColor(200, 255, 200))  # Light green
            elif status == 'absent':
                status_item.setBackground(QColor(255, 200, 200))  # Light red
            elif status == 'late':
                status_item.setBackground(QColor(255, 255, 200))  # Light yellow
                
            self.students_table.setItem(row, 1, status_item)
            
            # Email column - Display parent email if available
            parent_email = student.parent_email or 'Not set'
            email_item = QTableWidgetItem(parent_email)
            self.students_table.setItem(row, 2, email_item)
            
            # Actions column with attendance buttons and notification
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(2, 2, 2, 2)
            
            if self.current_user.role in ['admin', 'teacher']:
                # Add attendance buttons
                present_button = QPushButton('Present')
                present_button.clicked.connect(lambda _, s_id=student.id: self.mark_attendance(s_id, 'present'))
                present_button.setMaximumWidth(70)
                actions_layout.addWidget(present_button)
                
                absent_button = QPushButton('Absent')
                absent_button.clicked.connect(lambda _, s_id=student.id: self.mark_attendance(s_id, 'absent'))
                absent_button.setMaximumWidth(70)
                actions_layout.addWidget(absent_button)
                
                late_button = QPushButton('Late')
                late_button.clicked.connect(lambda _, s_id=student.id: self.mark_attendance(s_id, 'late'))
                late_button.setMaximumWidth(70)
                actions_layout.addWidget(late_button)
                
                # Add notify button if student is marked absent or late
                if status in ['absent', 'late']:
                    notify_button = QPushButton('Notify')
                    notify_button.clicked.connect(lambda _, s_id=student.id: self.send_absence_notification(s_id))
                    notify_button.setMaximumWidth(70)
                    actions_layout.addWidget(notify_button)
            else:
                actions_label = QLabel('No actions available')
                actions_layout.addWidget(actions_label)
                
            actions_widget.setLayout(actions_layout)
            self.students_table.setCellWidget(row, 3, actions_widget)
            
            # Actions are now handled in the combined actions column above
        
        self.students_table.resizeColumnsToContents()
    
    def load_tasks(self):
        # Load classroom tasks for teachers/admins
        tasks = db_session.query(ClassroomTask).filter_by(classroom_id=self.classroom_id).order_by(ClassroomTask.created_date.desc()).all()
        self.tasks_table.setRowCount(len(tasks))
        
        for row, task in enumerate(tasks):
            # Title
            title_item = QTableWidgetItem(task.title)
            self.tasks_table.setItem(row, 0, title_item)
            
            # Description (truncated)
            desc = task.description if len(task.description) < 50 else task.description[:47] + '...'
            desc_item = QTableWidgetItem(desc)
            self.tasks_table.setItem(row, 1, desc_item)
            
            # Due Date
            due_date = task.due_date.strftime('%Y-%m-%d') if task.due_date else 'No due date'
            due_date_item = QTableWidgetItem(due_date)
            self.tasks_table.setItem(row, 2, due_date_item)
            
            # Created Date
            created_date = task.created_date.strftime('%Y-%m-%d')
            created_date_item = QTableWidgetItem(created_date)
            self.tasks_table.setItem(row, 3, created_date_item)
            
            # Actions
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            
            view_btn = QPushButton('View Submissions')
            view_btn.clicked.connect(lambda _, t_id=task.id: self.view_submissions(t_id))
            actions_layout.addWidget(view_btn)
            
            actions_widget.setLayout(actions_layout)
            self.tasks_table.setCellWidget(row, 4, actions_widget)
        
        self.tasks_table.resizeColumnsToContents()
    
    def load_student_tasks(self):
        # Load classroom tasks for students
        tasks = db_session.query(ClassroomTask).filter_by(classroom_id=self.classroom_id).order_by(ClassroomTask.created_date.desc()).all()
        self.tasks_table.setRowCount(len(tasks))
        
        # Get student's submissions
        submissions = db_session.query(Task).filter_by(user_id=self.current_user.id).all()
        submission_dict = {submission.classroom_task_id: submission for submission in submissions if submission.classroom_task_id}
        
        for row, task in enumerate(tasks):
            # Title
            title_item = QTableWidgetItem(task.title)
            self.tasks_table.setItem(row, 0, title_item)
            
            # Description (truncated)
            desc = task.description if len(task.description) < 50 else task.description[:47] + '...'
            desc_item = QTableWidgetItem(desc)
            self.tasks_table.setItem(row, 1, desc_item)
            
            # Due Date
            due_date = task.due_date.strftime('%Y-%m-%d') if task.due_date else 'No due date'
            due_date_item = QTableWidgetItem(due_date)
            self.tasks_table.setItem(row, 2, due_date_item)
            
            # Status
            status = 'Submitted' if task.id in submission_dict else 'Not submitted'
            status_item = QTableWidgetItem(status)
            
            if status == 'Submitted':
                status_item.setBackground(QColor(200, 255, 200))  # Light green
            else:
                status_item.setBackground(QColor(255, 255, 200))  # Light yellow
                
            self.tasks_table.setItem(row, 3, status_item)
            
            # Actions
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            
            submit_btn = QPushButton('Submit Response')
            submit_btn.clicked.connect(lambda _, t_id=task.id: self.submit_task_response(t_id))
            actions_layout.addWidget(submit_btn)
            
            actions_widget.setLayout(actions_layout)
            self.tasks_table.setCellWidget(row, 4, actions_widget)
        
        self.tasks_table.resizeColumnsToContents()
    
    def create_task(self):
        dialog = CreateClassroomTaskDialog(self.classroom_id)
        if dialog.exec_():
            self.load_tasks()
    
    def view_submissions(self, task_id):
        dialog = TaskSubmissionsDialog(task_id)
        dialog.exec_()
    
    def submit_task_response(self, task_id):
        dialog = SubmitTaskDialog(task_id, self.current_user.id)
        if dialog.exec_():
            self.load_student_tasks()
    
    def mark_attendance(self, student_id, status):
        # Check if attendance already marked today
        today = date.today()
        existing_record = db_session.query(Attendance).filter(
            Attendance.user_id == student_id,
            Attendance.classroom_id == self.classroom_id,
            Attendance.date >= today
        ).first()
        
        if existing_record:
            existing_record.status = status
        else:
            new_attendance = Attendance(user_id=student_id, classroom_id=self.classroom_id, status=status)
            db_session.add(new_attendance)
        
        db_session.commit()
        
        student = db_session.query(User).get(student_id)
        QMessageBox.information(self, 'Success', f'Attendance marked for {student.username} as {status}')
        
        self.load_students()
        
    def send_absence_notification(self, student_id):
        student = db_session.query(User).get(student_id)
        if not student.parent_email:
            QMessageBox.information(self, 'Parent Email Required', 
                                  f'No parent email is set for {student.username}. Please add a parent email first.')
            dialog = ParentEmailDialog(student)
            if dialog.exec_():
                self.load_students()
            return
            
        try:
            # Create email setup dialog
            email_dialog = EmailSetupDialog(student, self.classroom_id)
            if not email_dialog.exec_():
                return
                
            sender_email = email_dialog.sender_email
            sender_password = email_dialog.sender_password
            subject = email_dialog.subject
            message_body = email_dialog.message_body
            
            # Show sending status
            progress = QProgressDialog(f"Sending email to parent of {student.username}...", None, 0, 0, self)
            progress.setWindowTitle("Sending Email")
            progress.setWindowModality(Qt.WindowModal)
            progress.show()
            QApplication.processEvents()
            
            # Create message
            msg = MIMEMultipart()
            msg['From'] = sender_email
            msg['To'] = student.parent_email
            msg['Subject'] = subject
            
            # Attach message body
            msg.attach(MIMEText(message_body, 'plain'))
            
            try:
                # Connect to Gmail SMTP server
                server = smtplib.SMTP('smtp.gmail.com', 587)
                server.starttls()
                server.login(sender_email, sender_password)
                
                # Send email
                server.send_message(msg)
                server.quit()
                
                progress.close()
                QMessageBox.information(self, 'Success', 
                                      f'Absence notification sent to parent of {student.username} at {student.parent_email}')
            except smtplib.SMTPAuthenticationError:
                progress.close()
                QMessageBox.critical(self, 'Authentication Error', 
                                   'Email login failed. If using Gmail, make sure you are using an App Password, not your regular password.')
            except smtplib.SMTPException as smtp_error:
                progress.close()
                QMessageBox.critical(self, 'SMTP Error', f'Email server error: {str(smtp_error)}')
            except Exception as e:
                progress.close()
                QMessageBox.critical(self, 'Error', f'Failed to send email: {str(e)}')
                print(f"Email error: {str(e)}")
        except Exception as e:
            QMessageBox.critical(self, 'Error', f'Failed to prepare email: {str(e)}')
            print(f"Email setup error: {str(e)}")

# Parent Email Dialog
class ParentEmailDialog(QDialog):
    def __init__(self, student):
        super().__init__()
        self.student = student
        self.init_ui()
        
    def init_ui(self):
        self.setWindowTitle(f'Add Parent Email for {self.student.username}')
        self.setGeometry(300, 300, 400, 150)
        
        layout = QVBoxLayout()
        
        # Form layout
        form_layout = QFormLayout()
        
        # Email field
        self.email_input = QLineEdit()
        if self.student.parent_email:
            self.email_input.setText(self.student.parent_email)
        form_layout.addRow('Parent Email:', self.email_input)
        
        layout.addLayout(form_layout)
        
        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.save_email)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
        self.setLayout(layout)
        
    def save_email(self):
        email = self.email_input.text()
        
        if not email:
            QMessageBox.warning(self, 'Error', 'Email address is required')
            return
        
        # Simple email validation
        if '@' not in email or '.' not in email:
            QMessageBox.warning(self, 'Error', 'Please enter a valid email address')
            return
        
        self.student.parent_email = email
        db_session.commit()
        
        QMessageBox.information(self, 'Success', f'Parent email for {self.student.username} saved successfully')
        self.accept()

# Email Setup Dialog
class EmailSetupDialog(QDialog):
    def __init__(self, student, classroom_id):
        super().__init__()
        self.student = student
        self.classroom_id = classroom_id
        self.sender_email = ''
        self.sender_password = ''
        self.subject = ''
        self.message_body = ''
        self.init_ui()
        
    def init_ui(self):
        self.setWindowTitle('Email Setup')
        self.setGeometry(300, 300, 500, 400)
        
        layout = QVBoxLayout()
        
        # Information label
        info_label = QLabel('To send absence notifications, you need to provide your email credentials.')
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        # Gmail app password note
        note_label = QLabel('Note: For Gmail accounts, you need to use an App Password instead of your regular password. '
                           'Go to your Google Account > Security > App passwords to generate one.')
        note_label.setWordWrap(True)
        note_label.setStyleSheet('color: #666;')
        layout.addWidget(note_label)
        
        # Form layout
        form_layout = QFormLayout()
        
        # Sender email field
        self.email_input = QLineEdit()
        form_layout.addRow('Your Email:', self.email_input)
        
        # Password field
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        form_layout.addRow('Password/App Password:', self.password_input)
        
        # Get today's attendance status
        today = date.today()
        attendance_record = db_session.query(Attendance).filter(
            Attendance.user_id == self.student.id,
            Attendance.classroom_id == self.classroom_id,
            Attendance.date >= today
        ).first()
        
        attendance_status = attendance_record.status if attendance_record else 'Not marked'
        
        if attendance_status == 'absent':
            default_subject = f'Absence Notification for {self.student.username}'
            default_message = f"""Dear Parent/Guardian,

This is to inform you that {self.student.username} was marked absent today in class.

Please contact the school for more information.

Regards,
School Administration"""
        elif attendance_status == 'late':
            default_subject = f'Late Arrival Notification for {self.student.username}'
            default_message = f"""Dear Parent/Guardian,

This is to inform you that {self.student.username} was marked late today in class.

Please contact the school for more information.

Regards,
School Administration"""
        else:
            default_subject = f'Attendance Notification for {self.student.username}'
            default_message = f"""Dear Parent/Guardian,

This is to inform you about {self.student.username}'s attendance status in class.

Please contact the school for more information.

Regards,
School Administration"""
        
        # Subject field
        self.subject_input = QLineEdit()
        self.subject_input.setText(default_subject)
        form_layout.addRow('Subject:', self.subject_input)
        
        layout.addLayout(form_layout)
        
        # Message body
        message_group = QGroupBox('Message')
        message_layout = QVBoxLayout()
        
        self.message_input = QTextEdit()
        self.message_input.setText(default_message)
        message_layout.addWidget(self.message_input)
        
        message_group.setLayout(message_layout)
        layout.addWidget(message_group)
        
        # Save credentials checkbox
        self.save_credentials = QCheckBox('Save credentials for future use (not recommended on shared computers)')
        layout.addWidget(self.save_credentials)
        
        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.send_setup)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
        self.setLayout(layout)
        
    def send_setup(self):
        self.sender_email = self.email_input.text()
        self.sender_password = self.password_input.text()
        self.subject = self.subject_input.text()
        self.message_body = self.message_input.toPlainText()
        
        if not self.sender_email or not self.sender_password:
            QMessageBox.warning(self, 'Error', 'Email and password are required')
            return
        
        if not self.subject or not self.message_body:
            QMessageBox.warning(self, 'Error', 'Subject and message are required')
            return
        
        # Simple email validation
        if '@' not in self.sender_email or '.' not in self.sender_email:
            QMessageBox.warning(self, 'Error', 'Please enter a valid email address')
            return
            
        self.accept()

# Main Application Window
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.init_ui()
        
    def init_ui(self):
        self.setWindowTitle('Engage Portal System')
        self.setGeometry(100, 100, 800, 600)
        
        # Create stacked widget for different screens
        self.stacked_widget = QStackedWidget()
        
        # Create login screen
        self.login_screen = LoginWindow()
        self.login_screen.login_successful.connect(self.show_dashboard)
        
        # Add screens to stacked widget
        self.stacked_widget.addWidget(self.login_screen)
        
        self.setCentralWidget(self.stacked_widget)
        
    def show_dashboard(self, user):
        # Remove any existing dashboard
        if self.stacked_widget.count() > 1:
            widget = self.stacked_widget.widget(1)
            self.stacked_widget.removeWidget(widget)
            widget.deleteLater()
        
        # Store user in session
        from session import set
        set('user', user)
        
        # Create appropriate dashboard based on user role
        if user.role == 'admin':
            dashboard = AdminDashboard(user)
        elif user.role == 'teacher':
            dashboard = TeacherDashboard(user)
        else:  # student
            dashboard = StudentDashboard(user)
        
        # Add dashboard to stacked widget and show it
        self.stacked_widget.addWidget(dashboard)
        self.stacked_widget.setCurrentIndex(1)
    
    def show_login(self):
        self.stacked_widget.setCurrentIndex(0)

# Main function
def main():
    # Create database tables if they don't exist
    from sqlalchemy import inspect
    inspector = inspect(engine)
    
    # Ensure all required tables (including new ones) exist
    if not (inspector.has_table('classroom') and inspector.has_table('classroom_task') and inspector.has_table('classroom_membership')):
        from database import db
        import app
        with app.app.app_context():
            db.create_all()
            
            # Check if a default classroom exists
            default_classroom = db_session.query(Classroom).filter_by(name='Default Classroom').first()
            if not default_classroom:
                # Create a default classroom
                default_classroom = Classroom(name='Default Classroom', description='Default classroom for all students')
                db_session.add(default_classroom)
                db_session.commit()
                print("Default classroom created.")
            
            # Check if an admin user already exists
            admin = db_session.query(User).filter_by(username='admin').first()
            if not admin:
                # Create a default admin user if one doesn't exist
                print("Creating default admin user...")
                hashed_password = bcrypt.generate_password_hash('admin_password').decode('utf-8')
                admin_user = User(username='admin', password_hash=hashed_password, role='admin')
                db_session.add(admin_user)
                db_session.commit()
                print("Default admin user created with username 'admin' and password 'admin_password'.")
    
    app = QApplication(sys.argv)
    app.setStyle('Fusion')  # Use Fusion style for a modern look
    
    # Set application stylesheet for dark theme
    app.setStyleSheet("""
        QWidget {
            background-color: #2c2f33;
            color: #ffffff;
        }
        
        QPushButton {
            background-color: #7289da;
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 4px;
        }
        
        QPushButton:hover {
            background-color: #5b6eae;
        }
        
        QLineEdit, QTextEdit, QComboBox {
            background-color: #23272a;
            border: 1px solid #42464d;
            padding: 8px;
            border-radius: 4px;
        }
        
        QTableWidget {
            background-color: #23272a;
            border: 1px solid #42464d;
        }
        
        QTableWidget::item {
            padding: 8px;
        }
        
        QHeaderView::section {
            background-color: #42464d;
            color: white;
            padding: 8px;
            border: none;
        }
        
        QTabWidget::pane {
            border: 1px solid #42464d;
        }
        
        QTabBar::tab {
            background-color: #23272a;
            color: white;
            padding: 8px 16px;
            border-top-left-radius: 4px;
            border-top-right-radius: 4px;
        }
        
        QTabBar::tab:selected {
            background-color: #7289da;
        }
        
        QGroupBox {
            border: 1px solid #42464d;
            border-radius: 4px;
            margin-top: 1em;
        }
        
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 5px;
        }
    """)
    
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()