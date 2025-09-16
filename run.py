#!/usr/bin/env python
# run.py - Launcher for Engage Portal System

import os
import sys
import subprocess

def clear_screen():
    """Clear the console screen."""
    os.system('cls' if os.name == 'nt' else 'clear')

def print_header():
    """Print the application header."""
    clear_screen()
    print("====================================")
    print("       ENGAGE PORTAL SYSTEM        ")
    print("====================================")
    print()

def main():
    """Main function to launch the application."""
    while True:
        print_header()
        print("Please select an option:")
        print("1. Run Web Application")
        print("2. Run Desktop Application")
        print("3. Exit")
        print()
        
        choice = input("Enter your choice (1-3): ")
        
        if choice == '1':
            print("\nStarting web application...")
            print("Access the application at http://127.0.0.1:5000/")
            print("Press Ctrl+C to stop the server.\n")
            try:
                subprocess.run([sys.executable, 'app.py'])
            except KeyboardInterrupt:
                print("\nWeb server stopped.")
        
        elif choice == '2':
            print("\nStarting desktop application...\n")
            try:
                subprocess.run([sys.executable, 'desktop_app.py'])
            except Exception as e:
                print(f"\nError: {e}")
        
        elif choice == '3':
            print("\nExiting Engage Portal System. Goodbye!")
            break
        
        else:
            print("\nInvalid choice. Please try again.")
            input("Press Enter to continue...")

if __name__ == '__main__':
    main()