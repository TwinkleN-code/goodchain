import os
from auth import User
from database import Database
from keys import *
from utils import print_header
from recover_key import recover_private_key

user = User()
db = Database()

def settings_menu():
    print_header(user.current_user)
    options = [
        {"option": "1", "text": "Change username", "action": lambda: user.change_username()},
        {"option": "2", "text": "Change password", "action": lambda: user.change_password()},
        {"option": "3", "text": "Delete account", "action": lambda: user.delete_account()},
        {"option": "4", "text": "Back to main menu", "action": lambda: "back"}
    ]

    max_option_length = max(len(opt['text']) for opt in options) + 6
    while True:
        print ("┌" + "─" * max_option_length + "┐")
        for opt in options: 
            spaces_required = max_option_length - len(opt['text']) - 4
            print(f"│ {opt['option']}. {opt['text']}" + ' ' * spaces_required + "│")
        print ("└" + "─" * max_option_length + "┘")
        choice = input('> ')

        action = next((opt['action'] for opt in options if opt['option'] == choice), None)
        if action and action() == "back":
            print_header(user.current_user)
            break
        elif not action:
            print_header(user.current_user)
            print('Invalid choice')

def display_menu(is_logged_in):
    if is_logged_in:
        return [
            # {"option": "1", "text": "View keys", "action": lambda: view_user_keys(user.current_user)}, 
            # {"option": "1", "text": "Send coins", "action": lambda: user.send_coins()},
            {"option": "1", "text": "Account Settings", "action": lambda: settings_menu()},
            {"option": "2", "text": "View balance", "action": lambda: user.view_balance()},
            {"option": "3", "text": "View transactions", "action": lambda: user.view_transactions()},
            {"option": "4", "text": "Logout", "action": lambda: user.logout()},
            {"option": "5", "text": "Exit application", "action": lambda: "exit"}
        ]
    else:
        return [
            {"option": "1", "text": "Register", "action": lambda: user.register()},
            {"option": "2", "text": "Login", "action": lambda: user.login()},          
            {"option": "3", "text": "Recover private key", "action": lambda: recover_private_key()},
            {"option": "4", "text": "Exit application", "action": lambda: "exit"}
        ]

def main_menu():
    print_header()
    while True:
        options = display_menu(user.current_user)

        # draw box
        max_option_length = max(len(opt['text']) for opt in options) + 6
        print ("┌" + "─" * max_option_length + "┐")
        for opt in options: 
            spaces_required = max_option_length - len(opt['text']) - 4
            print(f"│ {opt['option']}. {opt['text']}" + ' ' * spaces_required + "│")
        print ("└" + "─" * max_option_length + "┘")
        choice = input('> ')

        # choose action
        action = next((opt['action'] for opt in options if opt['option'] == choice), None)
        if action and action() == "exit":
            break          
        elif not action:
            print_header(user.current_user)
            print('Invalid choice')

db.setup()

# create key if not exists
if not os.path.isfile('key.txt'):
    key = generate_key()
    save_key(key)
    
main_menu()