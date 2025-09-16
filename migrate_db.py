# migrate_db.py

import os
import sqlite3
from app import app, db
from database import User, Classroom, Attendance, Task

# Get the database path from the app config
db_path = app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')

# Check if the database file exists
if os.path.exists(db_path):
    print(f"Database found at {db_path}")
    
    # Create a backup of the existing database
    backup_path = db_path + '.backup'
    print(f"Creating backup at {backup_path}")
    with open(db_path, 'rb') as src, open(backup_path, 'wb') as dst:
        dst.write(src.read())
    
    # Connect to the database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check if classroom table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='classroom'")
    if not cursor.fetchone():
        print("Creating classroom table...")
        cursor.execute("""
        CREATE TABLE classroom (
            id INTEGER PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            description VARCHAR(255),
            teacher_id INTEGER,
            FOREIGN KEY (teacher_id) REFERENCES user (id)
        )
        """)
    else:
        print("Classroom table already exists")
    
    # Check if user table has classroom_id column
    cursor.execute("PRAGMA table_info(user)")
    columns = [column[1] for column in cursor.fetchall()]
    
    if 'classroom_id' not in columns:
        print("Adding classroom_id column to user table...")
        cursor.execute("ALTER TABLE user ADD COLUMN classroom_id INTEGER REFERENCES classroom(id)")
    else:
        print("classroom_id column already exists in user table")
        
    # Check if user table has parent_email column
    if 'parent_email' not in columns:
        print("Adding parent_email column to user table...")
        cursor.execute("ALTER TABLE user ADD COLUMN parent_email VARCHAR(120)")
    else:
        print("parent_email column already exists in user table")
    
    # Check if attendance table has classroom_id column
    cursor.execute("PRAGMA table_info(attendance)")
    columns = [column[1] for column in cursor.fetchall()]
    
    if 'classroom_id' not in columns:
        print("Adding classroom_id column to attendance table...")
        cursor.execute("ALTER TABLE attendance ADD COLUMN classroom_id INTEGER NOT NULL DEFAULT 1 REFERENCES classroom(id)")
    else:
        print("classroom_id column already exists in attendance table")
    
    # Create a default classroom if none exists
    cursor.execute("SELECT COUNT(*) FROM classroom")
    if cursor.fetchone()[0] == 0:
        print("Creating default classroom...")
        cursor.execute("INSERT INTO classroom (name, description) VALUES (?, ?)", 
                       ("Default Classroom", "Default classroom for all students"))
    
    # Commit changes and close connection
    conn.commit()
    conn.close()
    print("Database migration completed successfully!")
    
else:
    print(f"Database not found at {db_path}. Creating new database...")
    with app.app_context():
        db.create_all()
        print("New database created successfully!")
        
        # Create a default classroom
        default_classroom = Classroom(name="Default Classroom", description="Default classroom for all students")
        db.session.add(default_classroom)
        db.session.commit()
        print("Default classroom created.")

print("Migration complete!")