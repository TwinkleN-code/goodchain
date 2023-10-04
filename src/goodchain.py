from auth import register_user, login_user, logout_user
from database import setup_db
from utils import print_header

current_user = None

def display_menu(is_logged_in):
    if is_logged_in:
        return [
            {"option": "1", "text": "Logout", "action": lambda: logout_and_clear_user()},
            {"option": "2", "text": "Exit", "action": lambda: "exit"}
        ]
    else:
        return [
            {"option": "1", "text": "Register", "action": lambda: register_user()},
            {"option": "2", "text": "Login", "action": lambda: login_and_set_user()},
            {"option": "3", "text": "Exit", "action": lambda: "exit"}
        ]
    
def logout_and_clear_user():
    global current_user
    logout_user()
    current_user = None

def login_and_set_user():
    global current_user
    current_user = login_user()
    return current_user

def main_menu():
    global current_user
    print_header()
    while True:
        options = display_menu(current_user)
        for opt in options: 
            print(f"| {opt['option']}. {opt['text']} |")
        choice = input('> ')

        action = next((opt['action'] for opt in options if opt['option'] == choice), None)
        if action and action() == "exit":
            break
        elif not action:
            print_header(current_user)
            print('Invalid choice')

setup_db()

main_menu()