# Engage Portal System

A comprehensive classroom management system with both web and desktop interfaces. This application allows administrators to manage classrooms and users, teachers to track attendance, and students to submit tasks.

## Features

- User authentication with role-based access (Admin, Teacher, Student)
- Classroom management
- Attendance tracking
- Task submission for students
- Available as both web application and desktop application

## Installation

1. Clone this repository
2. Install the required dependencies:

```
pip install -r requirements.txt
```

## Running the Web Application

To run the web application:

```
python app.py
```

This will start the Flask development server at http://127.0.0.1:5000/

## Running the Desktop Application

To run the desktop application:

```
python desktop_app.py
```

This will launch the PyQt5-based desktop interface.

## Default Credentials

The system is initialized with a default admin account:

- Username: admin
- Password: admin_password

## Database

The application uses SQLite for data storage. The database file is located at `instance/site.db`.

## Project Structure

- `app.py`: Web application entry point
- `desktop_app.py`: Desktop application entry point
- `database.py`: Database models and configuration
- `templates/`: HTML templates for the web interface
- `static/`: CSS and other static files for the web interface

## Usage

### Admin

- Create and manage classrooms
- Create and manage users (teachers and students)
- Assign teachers to classrooms
- Assign students to classrooms
- View classroom details and mark attendance

### Teacher

- View assigned classrooms
- Mark student attendance
- View student details

### Student

- View classroom information
- Submit tasks
- View submitted tasks