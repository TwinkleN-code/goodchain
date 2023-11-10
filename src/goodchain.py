import os
import pickle
from auth import User
from database import Database
from notifications import notification
from block_validation import validation_chain
from transaction import Transaction
from keys import *
from recover_key import recover_private_key
from utils import print_header, display_menu_and_get_choice
from blockchain import Blockchain

user = User()
db = Database()
transaction = Transaction()
blockchain = Blockchain()

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
            {"option": "1", "text": " View keys", "action": lambda: view_user_keys(user.current_user)}, 
            {"option": "2", "text": " Account Settings", "action": lambda: settings_menu()},          
            {"option": "3", "text": " View transaction pool", "action": lambda: transaction.view_transactions(user.current_user)},
            {"option": "4", "text": " View blockchain", "action": lambda: blockchain.view_blockchain(user.current_user)},
            {"option": "5", "text": " Send coins", "action": lambda: user.transfer_coins()},
            {"option": "6", "text": " Cancel a transaction", "action": lambda: user.remove_transaction()},
            {"option": "7", "text": " Modify a transaction", "action": lambda: user.edit_transaction()},
            {"option": "8", "text": " Mine transactions", "action": lambda: blockchain.mine_transactions(user.current_user)},
            {"option": "9", "text": " Notifications", "action": lambda: notification.view_notifications(user.current_user)},
            {"option": "10", "text": "Check validation blockchain", "action": lambda: validation_chain(user.current_user)},
            {"option": "11", "text": "Logout", "action": lambda: user.logout()},
            {"option": "12", "text": "Exit application", "action": lambda: "exit"}
        ]
    else:
        return [
            {"option": "1", "text": "Register", "action": lambda: user.register()},
            {"option": "2", "text": "Login", "action": lambda: user.login()},          
            {"option": "3", "text": "Recover private key", "action": lambda: recover_private_key()},
            {"option": "4", "text": "View blockchain", "action": lambda: blockchain.view_blockchain()},
            {"option": "5", "text": "Exit application", "action": lambda: "exit"}
        ]

def main_menu():
    print_header()
    while True:
        options = display_menu(user.current_user is not None) # Assuming that user.current_user is None when not logged in
        choice_result = display_menu_and_get_choice(options, user.current_user)
        if choice_result == "exit":
            break         

db.setup()

# create key and files if not exists
if not os.path.isfile('key.txt'):
    key = generate_key()
    save_key(key)
if not os.path.isfile('blockchain.dat'):
    data = []
    with open("blockchain.dat", 'wb') as file:
        pickle.dump(data, file)
if not os.path.isfile('transactions.dat'):
    data = []
    with open("transactions.dat", "wb") as file:
        pickle.dump(data, file) 
main_menu()