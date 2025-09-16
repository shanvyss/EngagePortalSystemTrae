from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
                             QTextEdit, QPushButton, QMessageBox, QFileDialog,
                             QGroupBox, QGridLayout)
import os
import time
import shutil
from datetime import datetime
from database import ClassroomTask, Task, db_session

# Define UPLOAD_FOLDER for file uploads
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')

# Create upload folder if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

class SubmitTaskDialog(QDialog):
    def __init__(self, task_id, user_id):
        super().__init__()
        self.task_id = task_id
        self.user_id = user_id
        self.file_path = None
        self.setWindowTitle('Submit Task Response')
        self.setGeometry(300, 300, 600, 500)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()

        # Task information
        task = db_session.query(ClassroomTask).filter_by(id=self.task_id).first()
        if not task:
            QMessageBox.warning(self, 'Error', 'Task not found')
            self.reject()
            return

        # Check if already submitted
        existing_submission = db_session.query(Task).filter_by(
            user_id=self.user_id, 
            classroom_task_id=self.task_id
        ).first()

        # Task details
        task_info_layout = QGridLayout()
        task_info_layout.addWidget(QLabel('Title:'), 0, 0)
        task_info_layout.addWidget(QLabel(task.title), 0, 1)
        task_info_layout.addWidget(QLabel('Description:'), 1, 0)
        task_info_layout.addWidget(QLabel(task.description), 1, 1)
        task_info_layout.addWidget(QLabel('Due Date:'), 2, 0)
        task_info_layout.addWidget(QLabel(task.due_date.strftime('%Y-%m-%d') if task.due_date else 'No due date'), 2, 1)
        
        task_info_group = QGroupBox('Task Information')
        task_info_group.setLayout(task_info_layout)
        layout.addWidget(task_info_group)

        # Response content
        self.content_label = QLabel('Your Response:')
        layout.addWidget(self.content_label)
        self.content_input = QTextEdit()
        if existing_submission and existing_submission.content:
            self.content_input.setPlainText(existing_submission.content)
        layout.addWidget(self.content_input)

        # File upload
        file_layout = QHBoxLayout()
        self.file_label = QLabel('Attach File (Optional):')
        file_layout.addWidget(self.file_label)
        
        self.file_path_display = QLineEdit()
        self.file_path_display.setReadOnly(True)
        if existing_submission and existing_submission.file_path:
            self.file_path_display.setText(existing_submission.file_path)
            self.file_path = existing_submission.file_path
        file_layout.addWidget(self.file_path_display)
        
        self.browse_button = QPushButton('Browse...')
        self.browse_button.clicked.connect(self.browse_file)
        file_layout.addWidget(self.browse_button)
        
        layout.addLayout(file_layout)

        # Buttons
        button_layout = QHBoxLayout()
        self.submit_button = QPushButton('Submit Response')
        self.submit_button.clicked.connect(self.submit_response)
        self.cancel_button = QPushButton('Cancel')
        self.cancel_button.clicked.connect(self.reject)

        button_layout.addWidget(self.submit_button)
        button_layout.addWidget(self.cancel_button)

        layout.addLayout(button_layout)
        self.setLayout(layout)

        # Update button text if this is an update
        if existing_submission:
            self.submit_button.setText('Update Response')
            self.setWindowTitle('Update Task Response')

    def browse_file(self):
        file_dialog = QFileDialog()
        file_path, _ = file_dialog.getOpenFileName(
            self, 'Select File', '', 
            'All Files (*);;Documents (*.pdf *.docx *.txt);;Images (*.png *.jpg *.jpeg)'
        )
        
        if file_path:
            self.file_path = file_path
            self.file_path_display.setText(file_path)

    def submit_response(self):
        content = self.content_input.toPlainText().strip()
        
        # Require either content or file
        if not content and not self.file_path:
            QMessageBox.warning(self, 'Error', 'Please provide either a text response or attach a file')
            return

        # Check if already submitted
        existing_submission = db_session.query(Task).filter_by(
            user_id=self.user_id, 
            classroom_task_id=self.task_id
        ).first()

        try:
            # Get classroom ID from the task
            task = db_session.query(ClassroomTask).filter_by(id=self.task_id).first()
            if not task:
                QMessageBox.warning(self, 'Error', 'Task not found')
                return
                
            # Process file if provided
            saved_file_path = None
            file_type = None
            
            if self.file_path:
                # Create upload folder if it doesn't exist
                os.makedirs(UPLOAD_FOLDER, exist_ok=True)
                
                # Get file extension and generate secure filename
                _, file_extension = os.path.splitext(self.file_path)
                secure_filename = f"{self.user_id}_{self.task_id}_{int(time.time())}{file_extension}"
                saved_file_path = secure_filename
                
                # Determine file type
                if file_extension.lower() in ['.jpg', '.jpeg', '.png', '.gif', '.bmp']:
                    file_type = 'image'
                elif file_extension.lower() in ['.pdf', '.doc', '.docx', '.txt', '.rtf']:
                    file_type = 'document'
                else:
                    file_type = 'file'
                
                # Copy file to upload folder
                shutil.copy2(self.file_path, os.path.join(UPLOAD_FOLDER, secure_filename))
            
            if existing_submission:
                # Update existing submission
                existing_submission.content = content
                if saved_file_path:
                    # If there was a previous file, we could delete it here
                    existing_submission.file_path = saved_file_path
                    existing_submission.file_type = file_type
                existing_submission.date = datetime.now()
                db_session.commit()
                QMessageBox.information(self, 'Success', 'Task response updated successfully')
            else:
                # Create new submission
                new_submission = Task(
                    user_id=self.user_id,
                    classroom_task_id=self.task_id,
                    content=content,
                    file_path=saved_file_path,
                    file_type=file_type,
                    date=datetime.now()
                )
                db_session.add(new_submission)
                db_session.commit()
                QMessageBox.information(self, 'Success', 'Task response submitted successfully')
            
            self.accept()
            
        except Exception as e:
            db_session.rollback()
            QMessageBox.warning(self, 'Error', f'Failed to submit response: {str(e)}')