from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit, 
                             QPushButton, QMessageBox, QTableWidget, QTableWidgetItem,
                             QHeaderView, QGroupBox, QGridLayout, QWidget)
import os
from database import ClassroomTask, Task, User, db_session

# Define UPLOAD_FOLDER for file access
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')

class TaskSubmissionsDialog(QDialog):
    def __init__(self, task_id):
        super().__init__()
        self.task_id = task_id
        self.setWindowTitle('Task Submissions')
        self.setGeometry(300, 300, 800, 600)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()

        # Task information
        task = db_session.query(ClassroomTask).filter_by(id=self.task_id).first()
        if not task:
            QMessageBox.warning(self, 'Error', 'Task not found')
            self.reject()
            return

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

        # Submissions table
        self.submissions_table = QTableWidget()
        self.submissions_table.setColumnCount(5)
        self.submissions_table.setHorizontalHeaderLabels(['Student', 'Date', 'Content', 'File', 'Actions'])
        self.submissions_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.submissions_table)

        # Load submissions
        self.load_submissions()

        # Close button
        self.close_button = QPushButton('Close')
        self.close_button.clicked.connect(self.accept)
        layout.addWidget(self.close_button)

        self.setLayout(layout)

    def load_submissions(self):
        submissions = db_session.query(Task).filter_by(classroom_task_id=self.task_id).all()
        self.submissions_table.setRowCount(len(submissions))

        for row, submission in enumerate(submissions):
            # Get student info
            student = db_session.query(User).filter_by(id=submission.user_id).first()
            student_name = student.username if student else 'Unknown'
            student_item = QTableWidgetItem(student_name)
            self.submissions_table.setItem(row, 0, student_item)

            # Submission date
            date_item = QTableWidgetItem(submission.date.strftime('%Y-%m-%d %H:%M'))
            self.submissions_table.setItem(row, 1, date_item)

            # Content (truncated)
            content = submission.content if submission.content else 'No text content'
            if len(content) > 50:
                content = content[:47] + '...'
            content_item = QTableWidgetItem(content)
            self.submissions_table.setItem(row, 2, content_item)

            # File
            file_info = 'No file' if not submission.file_path else f'{submission.file_type} file'
            file_item = QTableWidgetItem(file_info)
            self.submissions_table.setItem(row, 3, file_item)

            # Actions
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)

            if submission.file_path:
                view_btn = QPushButton('View File')
                view_btn.clicked.connect(lambda _, path=submission.file_path: self.view_file(path))
                actions_layout.addWidget(view_btn)

            view_details_btn = QPushButton('Details')
            view_details_btn.clicked.connect(lambda _, s=submission: self.view_submission_details(s))
            actions_layout.addWidget(view_details_btn)

            actions_widget.setLayout(actions_layout)
            self.submissions_table.setCellWidget(row, 4, actions_widget)

    def view_file(self, file_path):
        # Open the file with the default application
        try:
            os.startfile(os.path.join(UPLOAD_FOLDER, file_path))
        except Exception as e:
            QMessageBox.warning(self, 'Error', f'Could not open file: {str(e)}')

    def view_submission_details(self, submission):
        dialog = QDialog(self)
        dialog.setWindowTitle('Submission Details')
        dialog.setGeometry(350, 350, 600, 400)

        layout = QVBoxLayout()

        # Student info
        student = db_session.query(User).filter_by(id=submission.user_id).first()
        student_name = student.username if student else 'Unknown'
        layout.addWidget(QLabel(f'Student: {student_name}'))
        layout.addWidget(QLabel(f'Submitted: {submission.date.strftime("%Y-%m-%d %H:%M")}'))

        # Content
        content_group = QGroupBox('Submission Content')
        content_layout = QVBoxLayout()
        content_text = QTextEdit()
        content_text.setPlainText(submission.content if submission.content else 'No text content')
        content_text.setReadOnly(True)
        content_layout.addWidget(content_text)
        content_group.setLayout(content_layout)
        layout.addWidget(content_group)

        # File info
        if submission.file_path:
            file_group = QGroupBox('File Attachment')
            file_layout = QVBoxLayout()
            file_layout.addWidget(QLabel(f'File Type: {submission.file_type}'))
            file_layout.addWidget(QLabel(f'File Path: {submission.file_path}'))
            
            open_file_btn = QPushButton('Open File')
            open_file_btn.clicked.connect(lambda: self.view_file(submission.file_path))
            file_layout.addWidget(open_file_btn)
            
            file_group.setLayout(file_layout)
            layout.addWidget(file_group)

        # Close button
        close_btn = QPushButton('Close')
        close_btn.clicked.connect(dialog.accept)
        layout.addWidget(close_btn)

        dialog.setLayout(layout)
        dialog.exec_()