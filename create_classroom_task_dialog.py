from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
                             QTextEdit, QPushButton, QMessageBox, QDateEdit, QCheckBox)
from PyQt5.QtCore import Qt, QDate
from datetime import datetime
from database import ClassroomTask, db_session
from session import get, set

class CreateClassroomTaskDialog(QDialog):
    def __init__(self, classroom_id):
        super().__init__()
        self.classroom_id = classroom_id
        self.setWindowTitle('Create Classroom Task')
        self.setGeometry(300, 300, 500, 400)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()

        # Title
        self.title_label = QLabel('Task Title:')
        layout.addWidget(self.title_label)
        self.title_input = QLineEdit()
        layout.addWidget(self.title_input)

        # Description
        self.desc_label = QLabel('Task Description:')
        layout.addWidget(self.desc_label)
        self.desc_input = QTextEdit()
        layout.addWidget(self.desc_input)

        # Due Date
        self.due_date_label = QLabel('Due Date (Optional):')
        layout.addWidget(self.due_date_label)
        self.due_date_input = QDateEdit()
        self.due_date_input.setDate(QDate.currentDate().addDays(7))  # Default to 1 week from now
        self.due_date_input.setCalendarPopup(True)
        layout.addWidget(self.due_date_input)

        # Due Date Checkbox
        self.use_due_date = QCheckBox('Set Due Date')
        self.use_due_date.setChecked(True)
        self.use_due_date.stateChanged.connect(self.toggle_due_date)
        layout.addWidget(self.use_due_date)

        # Buttons
        button_layout = QHBoxLayout()
        self.create_button = QPushButton('Create Task')
        self.create_button.clicked.connect(self.create_task)
        self.cancel_button = QPushButton('Cancel')
        self.cancel_button.clicked.connect(self.reject)

        button_layout.addWidget(self.create_button)
        button_layout.addWidget(self.cancel_button)

        layout.addLayout(button_layout)
        self.setLayout(layout)

    def toggle_due_date(self, state):
        self.due_date_input.setEnabled(state == Qt.Checked)

    def create_task(self):
        title = self.title_input.text().strip()
        description = self.desc_input.toPlainText().strip()

        if not title or not description:
            QMessageBox.warning(self, 'Error', 'Please provide both title and description')
            return

        # Get the current user (teacher)
        current_user = get('user')
        if not current_user or current_user.role not in ['teacher', 'admin']:
            QMessageBox.warning(self, 'Error', 'You do not have permission to create tasks')
            return

        # Create the task
        new_task = ClassroomTask(
            title=title,
            description=description,
            classroom_id=self.classroom_id,
            teacher_id=current_user.id,
            created_date=datetime.now(),
            due_date=self.due_date_input.date().toPyDate() if self.use_due_date.isChecked() else None
        )

        try:
            db_session.add(new_task)
            db_session.commit()
            QMessageBox.information(self, 'Success', 'Task created successfully')
            self.accept()
        except Exception as e:
            db_session.rollback()
            QMessageBox.warning(self, 'Error', f'Failed to create task: {str(e)}')