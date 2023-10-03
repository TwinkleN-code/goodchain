import hashlib
import sqlite3
import re
import getpass
from utils import print_header

def validate_password(password):
    if 8 <= len(password) <= 32:
        if re.search('[a-z]', password) is not None:
            if re.search('[A-Z]', password) is not None:
                if re.search('[0-9]', password) is not None:
                    if re.search('[^a-zA-Z0-9]', password) is not None:
                        return True
                    
def validate_username(username):
    if 3 <= len(username) <= 32:
        if re.search('^[a-zA-Z0-9]+$', username) is not None:
            return True
                    
def username_exists(username):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('SELECT * FROM users WHERE username=?', (username,))
    retrieved_user = c.fetchone()
    conn.close()

    if retrieved_user is None:
        return False
    else:
        return True

def register_user():
    username = input('Enter a username: ').lower()

    if username_exists(username):
        print_header()
        print('Username is already taken')
        return
    
    if not validate_username(username):
        print_header()
        print('Username must be between 3 and 32 characters and contain only letters and numbers')
        return
    
    password = getpass.getpass('Enter a password: ')

    if not validate_password(password):
        print_header()
        print('Password must be between 8 and 32 characters and contain at least one lowercase letter, one uppercase letter, one number, and one special character')
        return
    
    confirm_password = getpass.getpass('Confirm password: ')

    while password != confirm_password:
        print_header()
        print('Passwords do not match')
        return

    hashed_pw = hashlib.sha256(password.encode()).hexdigest()

    conn = sqlite3.connect('users.db')
    c = conn.cursor()

    try:
        c.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, hashed_pw))
        conn.commit()
        print_header()
        print('Registration successful')
    except sqlite3.IntegrityError:
        print_header()
        print('Username is already taken')

    conn.close()

def login_user():
    username = input('Enter your username: ').lower()
    password = getpass.getpass('Enter your password: ')

    hashed_pw = hashlib.sha256(password.encode()).hexdigest()

    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('SELECT * FROM users WHERE username=? AND password=?', (username, hashed_pw))

    retrieved_user = c.fetchone()

    conn.close()

    if retrieved_user is None:
        print_header()
        print('Invalid username or password')
        return None
    else:
        print_header(username)
        print('Login successful')
        return username

def logout_user():
    print_header()
    print("You've been logged out")
    return None