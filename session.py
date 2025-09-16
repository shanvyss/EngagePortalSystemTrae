# session.py

# This module provides a simple session management system for the desktop application
# to store the current user information and other session data.

# Dictionary to store session data
session = {}

# Functions to manage session data
def set(key, value):
    """Set a value in the session"""
    session[key] = value

def get(key, default=None):
    """Get a value from the session"""
    return session.get(key, default)

def clear():
    """Clear all session data"""
    session.clear()

def remove(key):
    """Remove a specific key from the session"""
    if key in session:
        del session[key]