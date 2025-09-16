# app.py

from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory
from flask_login import LoginManager, login_user, logout_user, current_user, login_required
from flask_bcrypt import Bcrypt
from database import db, User, Attendance, Task, Classroom, ClassroomTask # Import all models
import os
from werkzeug.utils import secure_filename
from datetime import datetime

# Create the Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_super_secret_key' # Change this
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db' # Use a SQLite database
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# File upload configuration
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload size
app.config['ALLOWED_EXTENSIONS'] = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'doc', 'docx'}

# Create uploads directory if it doesn't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Initialize extensions
db.init_app(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# User loader for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# --- ROUTES ---

@app.route('/')
def home():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        # Parsing form data (Complexity 9)
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        
        if user and bcrypt.check_password_hash(user.password_hash, password):
            login_user(user, remember=True)
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password.', 'danger')
            
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    if current_user.role == 'admin':
        # Admin sees all classrooms and can manage them
        classrooms = Classroom.query.all()
        users = User.query.filter(User.role.in_(['student', 'teacher'])).all()
        return render_template('dashboard.html', classrooms=classrooms, users=users, is_admin=True)
    elif current_user.role == 'teacher':
        # Teacher sees only their assigned classrooms
        classrooms = Classroom.query.filter_by(teacher_id=current_user.id).all()
        return render_template('dashboard.html', classrooms=classrooms, is_teacher=True)
    else:
        # Student dashboard
        tasks = Task.query.filter_by(user_id=current_user.id).all()
        classroom = current_user.classroom
        return render_template('dashboard.html', tasks=tasks, classroom=classroom, is_student=True)

@app.route('/register', methods=['GET', 'POST'])
@login_required
def register():
    # Only admins can create accounts
    if current_user.role != 'admin':
        flash('You do not have permission to access this page.', 'danger')
        return redirect(url_for('dashboard'))
    
    classrooms = Classroom.query.all()
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        role = request.form.get('role', 'student')
        classroom_id = request.form.get('classroom_id')
        
        # Check if username already exists
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash(f'Username {username} already exists. Please choose a different username.', 'danger')
            return redirect(url_for('register'))
        
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        
        try:
            new_user = User(username=username, password_hash=hashed_password, role=role)
            
            # Assign classroom if provided and role is student or teacher
            if classroom_id and role in ['student', 'teacher']:
                new_user.classroom_id = classroom_id
                
                # If role is teacher, also set as classroom teacher
                if role == 'teacher':
                    classroom = Classroom.query.get(classroom_id)
                    if classroom:
                        classroom.teacher_id = new_user.id
            
            db.session.add(new_user)
            db.session.commit()
            
            flash(f'User {username} created successfully!', 'success')
            return redirect(url_for('dashboard'))
        except Exception as e:
            db.session.rollback()
            flash(f'An error occurred while creating the user: {str(e)}', 'danger')
            return redirect(url_for('register'))
        
    return render_template('register.html', classrooms=classrooms)

# Route for admin/teacher to mark attendance
@app.route('/mark_attendance/<int:classroom_id>/<int:user_id>/<string:status>')
@login_required
def mark_attendance(classroom_id, user_id, status):
    # Check if user is admin or the teacher of this classroom
    classroom = Classroom.query.get_or_404(classroom_id)
    
    if current_user.role != 'admin' and (current_user.role != 'teacher' or classroom.teacher_id != current_user.id):
        flash('You do not have permission to perform this action.', 'danger')
        return redirect(url_for('dashboard'))
    
    # Check if the student belongs to this classroom
    student = User.query.get_or_404(user_id)
    if student.classroom_id != classroom_id:
        flash('This student does not belong to this classroom.', 'danger')
        return redirect(url_for('classroom_details', classroom_id=classroom_id))
    
    new_attendance = Attendance(user_id=user_id, classroom_id=classroom_id, status=status)
    db.session.add(new_attendance)
    db.session.commit()
    flash(f'Attendance marked for {student.username} as {status}.', 'success')
    
    return redirect(url_for('classroom_details', classroom_id=classroom_id))

# Simplified route for students to submit a task
@app.route('/submit_task', methods=['POST'])
@login_required
def submit_task():
    if current_user.role != 'student':
        flash('You do not have permission to submit a task.', 'danger')
        return redirect(url_for('dashboard'))
    
    content = request.form.get('task_content')
    classroom_task_id = request.form.get('classroom_task_id')
    
    # Check if a file was uploaded
    file = request.files.get('task_file')
    file_path = None
    file_type = None
    
    if file and file.filename:
        if allowed_file(file.filename):
            # Secure the filename and save the file
            filename = secure_filename(file.filename)
            # Create a unique filename with timestamp
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            unique_filename = f"{timestamp}_{filename}"
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
            file.save(file_path)
            
            # Determine file type
            extension = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
            if extension in {'png', 'jpg', 'jpeg', 'gif'}:
                file_type = 'image'
            elif extension in {'doc', 'docx', 'pdf', 'txt'}:
                file_type = 'document'
            else:
                file_type = 'other'
        else:
            flash('File type not allowed.', 'danger')
            return redirect(url_for('dashboard'))
    
    # Create the task
    new_task = Task(
        user_id=current_user.id, 
        content=content,
        classroom_task_id=classroom_task_id if classroom_task_id else None,
        file_path=file_path,
        file_type=file_type
    )
    
    db.session.add(new_task)
    db.session.commit()
    
    flash('Task submitted successfully!', 'success')
    return redirect(url_for('dashboard'))

# Helper function to check if file extension is allowed
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

# Route to download uploaded files
@app.route('/uploads/<filename>')
@login_required
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# Route for teachers to create classroom tasks
@app.route('/create_classroom_task/<int:classroom_id>', methods=['GET', 'POST'])
@login_required
def create_classroom_task(classroom_id):
    # Check if user is a teacher or admin
    if current_user.role not in ['teacher', 'admin']:
        flash('You do not have permission to create classroom tasks.', 'danger')
        return redirect(url_for('dashboard'))
    
    # Check if teacher is assigned to this classroom or user is admin
    classroom = Classroom.query.get_or_404(classroom_id)
    if current_user.role == 'teacher' and classroom.teacher_id != current_user.id:
        flash('You can only create tasks for classrooms you teach.', 'danger')
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        due_date_str = request.form.get('due_date')
        
        if not title or not description:
            flash('Title and description are required.', 'danger')
            return redirect(url_for('create_classroom_task', classroom_id=classroom_id))
        
        # Parse due date if provided
        due_date = None
        if due_date_str:
            try:
                due_date = datetime.strptime(due_date_str, '%Y-%m-%d')
            except ValueError:
                flash('Invalid date format. Please use YYYY-MM-DD.', 'danger')
                return redirect(url_for('create_classroom_task', classroom_id=classroom_id))
        
        new_task = ClassroomTask(
            title=title,
            description=description,
            classroom_id=classroom_id,
            teacher_id=current_user.id,
            due_date=due_date
        )
        
        db.session.add(new_task)
        db.session.commit()
        
        flash(f'Task "{title}" created successfully!', 'success')
        return redirect(url_for('classroom_details', classroom_id=classroom_id))
    
    return render_template('create_classroom_task.html', classroom=classroom)

# Route to create a new classroom
@app.route('/create_classroom', methods=['GET', 'POST'])
@login_required
def create_classroom():
    if current_user.role != 'admin':
        flash('Only administrators can create classrooms.', 'danger')
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        teacher_id = request.form.get('teacher_id')
        
        if not name:
            flash('Classroom name is required.', 'danger')
            return redirect(url_for('create_classroom'))
        
        new_classroom = Classroom(name=name, description=description)
        
        # Assign teacher if provided
        if teacher_id:
            teacher = User.query.get(teacher_id)
            if teacher and teacher.role == 'teacher':
                new_classroom.teacher_id = teacher_id
        
        db.session.add(new_classroom)
        db.session.commit()
        flash(f'Classroom "{name}" created successfully!', 'success')
        return redirect(url_for('dashboard'))
    
    # Get all teachers for the dropdown
    teachers = User.query.filter_by(role='teacher').all()
    return render_template('create_classroom.html', teachers=teachers)

# Route to view classroom details
@app.route('/classroom/<int:classroom_id>')
@login_required
def classroom_details(classroom_id):
    classroom = Classroom.query.get_or_404(classroom_id)
    
    # Get all students in this classroom
    students = User.query.filter_by(classroom_id=classroom_id, role='student').all()
    
    # Get today's attendance records
    today = datetime.now().date()
    attendance_records = Attendance.query.filter(
        Attendance.classroom_id == classroom_id,
        Attendance.date >= today
    ).all()
    
    # Create a dictionary of user_id -> attendance status for easy lookup
    attendance_dict = {record.user_id: record.status for record in attendance_records}
    
    # Get classroom tasks
    classroom_tasks = ClassroomTask.query.filter_by(classroom_id=classroom_id).order_by(ClassroomTask.created_date.desc()).all()
    
    # For students, get their task submissions
    student_submissions = {}
    if current_user.role == 'student':
        submissions = Task.query.filter_by(user_id=current_user.id).all()
        student_submissions = {submission.classroom_task_id: submission for submission in submissions if submission.classroom_task_id}
    
    return render_template(
        'classroom_details.html',
        classroom=classroom,
        students=students,
        attendance_dict=attendance_dict,
        classroom_tasks=classroom_tasks,
        student_submissions=student_submissions
    )

# Route to view task submissions for a classroom task
@app.route('/classroom_task/<int:task_id>/submissions')
@login_required
def view_task_submissions(task_id):
    # Check if user is a teacher or admin
    if current_user.role not in ['teacher', 'admin']:
        flash('You do not have permission to view task submissions.', 'danger')
        return redirect(url_for('dashboard'))
    
    classroom_task = ClassroomTask.query.get_or_404(task_id)
    
    # Check if teacher is assigned to this classroom or user is admin
    if current_user.role == 'teacher' and classroom_task.teacher_id != current_user.id:
        flash('You can only view submissions for tasks you created.', 'danger')
        return redirect(url_for('dashboard'))
    
    # Get all submissions for this task
    submissions = Task.query.filter_by(classroom_task_id=task_id).all()
    
    # Get all students in the classroom
    students = User.query.filter_by(classroom_id=classroom_task.classroom_id, role='student').all()
    
    # Create a dictionary of user_id -> submission for easy lookup
    submission_dict = {submission.user_id: submission for submission in submissions}
    
    return render_template(
        'task_submissions.html',
        classroom_task=classroom_task,
        students=students,
        submission_dict=submission_dict
    )

# Route to view classroom attendance
@app.route('/classroom/<int:classroom_id>/attendance')
@login_required
def classroom_attendance(classroom_id):
    classroom = Classroom.query.get_or_404(classroom_id)
    
    # Check permissions
    if current_user.role == 'student' and current_user.classroom_id != classroom_id:
        flash('You do not have permission to view this classroom.', 'danger')
        return redirect(url_for('dashboard'))
    
    if current_user.role == 'teacher' and classroom.teacher_id != current_user.id:
        flash('You are not assigned to this classroom.', 'danger')
        return redirect(url_for('dashboard'))
    
    # Get students in this classroom
    students = User.query.filter_by(classroom_id=classroom_id, role='student').all()
    
    # Get today's attendance records
    from datetime import date
    today = date.today()
    attendance_records = Attendance.query.filter(
        Attendance.classroom_id == classroom_id,
        Attendance.date >= today
    ).all()
    
    # Create a dictionary of user_id -> attendance status for easy lookup
    attendance_dict = {record.user_id: record.status for record in attendance_records}
    
    return render_template('classroom_details.html', 
                           classroom=classroom, 
                           students=students, 
                           attendance_dict=attendance_dict,
                           is_admin=(current_user.role == 'admin'),
                           is_teacher=(current_user.role == 'teacher'))

# Route to assign students to a classroom
@app.route('/assign_classroom/<int:user_id>', methods=['POST'])
@login_required
def assign_classroom(user_id):
    if current_user.role != 'admin':
        flash('Only administrators can assign classrooms.', 'danger')
        return redirect(url_for('dashboard'))
    
    classroom_id = request.form.get('classroom_id')
    user = User.query.get_or_404(user_id)
    
    if user.role not in ['student', 'teacher']:
        flash('Only students and teachers can be assigned to classrooms.', 'danger')
        return redirect(url_for('dashboard'))
    
    user.classroom_id = classroom_id
    
    # If user is a teacher, also update the classroom's teacher_id
    if user.role == 'teacher' and classroom_id:
        classroom = Classroom.query.get(classroom_id)
        if classroom:
            classroom.teacher_id = user_id
    
    db.session.commit()
    flash(f'User {user.username} has been assigned to the classroom.', 'success')
    return redirect(url_for('dashboard'))
    
if __name__ == '__main__':
    # Create all tables
    with app.app_context():
        db.create_all()
        
        # Check if a default classroom exists
        default_classroom = Classroom.query.filter_by(name='Default Classroom').first()
        if not default_classroom:
            # Create a default classroom
            default_classroom = Classroom(name='Default Classroom', description='Default classroom for all students')
            db.session.add(default_classroom)
            db.session.commit()
            print("Default classroom created.")
        
        # Check if an admin user already exists
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            # Create a default admin user if one doesn't exist
            print("Creating default admin user...")
            hashed_password = bcrypt.generate_password_hash('admin_password').decode('utf-8')
            admin_user = User(username='admin', password_hash=hashed_password, role='admin')
            db.session.add(admin_user)
            db.session.commit()
            print("Default admin user created with username 'admin' and password 'admin_password'.")
        
    app.run(debug=True)