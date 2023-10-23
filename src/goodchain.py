import os
from auth import User
from database import Database
from keys import *
from recover_key import recover_private_key
from utils import print_header, display_menu_and_get_choice

user = User()
db = Database()

def settings_menu():
    print_header(user.current_user)
    options = [
        {"option": "1", "text": "Change username", "action": lambda: user.change_username()},
        {"option": "2", "text": "Change password", "action": lambda: user.change_password()},
        {"option": "3", "text": "Back to main menu", "action": lambda: "back"}
    ]

    display_menu_and_get_choice(options, user.current_user)

def display_menu(is_logged_in):
    if is_logged_in:
        return [
            {"option": "1", "text": "Send coins", "action": lambda: user.transfer_coins()},
            {"option": "2", "text": "View keys", "action": lambda: view_user_keys(user.current_user)}, 
            {"option": "3", "text": "Account Settings", "action": lambda: settings_menu()},
            {"option": "4", "text": "View balance", "action": lambda: user.view_balance()},           
            {"option": "5", "text": "View transactions", "action": lambda: user.view_transactions()},
            {"option": "6", "text": "Logout", "action": lambda: user.logout()},
            {"option": "7", "text": "Exit application", "action": lambda: "exit"}
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
        options = display_menu(user.current_user is not None) # Assuming that user.current_user is None when not logged in
        choice_result = display_menu_and_get_choice(options, user.current_user)
        if choice_result == "exit":
            break         

db.setup()

# create key if not exists
if not os.path.isfile('key.txt'):
    key = generate_key()
    save_key(key)
    
main_menu()