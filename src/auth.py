import hashlib
import sqlite3
import re

def validate_password(password):
    if 8 <= len(password) <= 32:
        if re.search('[a-z]', password) is not None:
            if re.search('[A-Z]', password) is not None:
                if re.search('[0-9]', password) is not None:
                    if re.search('[^a-zA-Z0-9]', password) is not None:
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
    username = input('Enter a username: ')

    if username_exists(username):
        print('Username is already taken')
        return
    
    password = input('Enter a password: ')

    if not validate_password(password):
        print('Password must be between 8 and 32 characters and contain at least one lowercase letter, one uppercase letter, one number, and one special character')
        return

    hashed_pw = hashlib.sha256(password.encode()).hexdigest()

    conn = sqlite3.connect('users.db')
    c = conn.cursor()

    try:
        c.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, hashed_pw))
        conn.commit()
        print('Registration successful')
    except sqlite3.IntegrityError:
        print('Username is already taken')

    conn.close()

def login_user():
    username = input('Enter your username: ')
    password = input('Enter your password: ')

    hashed_pw = hashlib.sha256(password.encode()).hexdigest()

    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('SELECT * FROM users WHERE username=? AND password=?', (username, hashed_pw))

    retrieved_user = c.fetchone()

    conn.close()

    if retrieved_user is None:
        print('Invalid username or password')
        return None
    else:
        print('Login successful')
        return username

def logout_user():
    print("You've been logged out")
    return None