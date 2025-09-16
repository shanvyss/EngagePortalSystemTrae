# reset_db.py

import os
import sqlite3

# Get the database path
db_path = 'site.db'

# Remove the existing database if it exists
if os.path.exists(db_path):
    print(f"Removing existing database at {db_path}")
    os.remove(db_path)

# Create a new database
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Create tables in the correct order to handle dependencies
print("Creating tables...")

# Create classroom table first
cursor.execute("""
CREATE TABLE classroom (
    id INTEGER PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description VARCHAR(255),
    teacher_id INTEGER,
    FOREIGN KEY (teacher_id) REFERENCES user (id)
)
""")

# Create user table
cursor.execute("""
CREATE TABLE user (
    id INTEGER PRIMARY KEY,
    username VARCHAR(80) NOT NULL UNIQUE,
    password_hash VARCHAR(128) NOT NULL,
    role VARCHAR(10) NOT NULL,
    classroom_id INTEGER,
    FOREIGN KEY (classroom_id) REFERENCES classroom (id)
)
""")

# Create attendance table
cursor.execute("""
CREATE TABLE attendance (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,
    classroom_id INTEGER NOT NULL,
    date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(10) NOT NULL,
    FOREIGN KEY (user_id) REFERENCES user (id),
    FOREIGN KEY (classroom_id) REFERENCES classroom (id)
)
""")

# Create task table
cursor.execute("""
CREATE TABLE task (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,
    content TEXT NOT NULL,
    date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES user (id)
)
""")

# Create a default classroom
print("Creating default classroom...")
cursor.execute("INSERT INTO classroom (name, description) VALUES (?, ?)", 
               ("Default Classroom", "Default classroom for all students"))

# Create a default admin user
print("Creating default admin user...")
# Using a pre-hashed password for 'admin_password'
hashed_password = '$2b$12$7gaKqZMMcZ481GkeSIvhM.yt.Za82i3qzXbNZW9wuOGctOA3nzBcW'
cursor.execute("INSERT INTO user (username, password_hash, role) VALUES (?, ?, ?)", 
               ("admin", hashed_password, "admin"))

# Commit changes and close connection
conn.commit()
conn.close()

print("Database reset complete!")