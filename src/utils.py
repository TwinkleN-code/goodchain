import os
from cryptography.exceptions import *
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec
from database import Database

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def display_menu_and_get_choice(options , username=None, *args):
    """Display menu based on the provided options and get user's choice."""
    max_option_length = max(len(opt['text']) for opt in options) + 6
    while True:
        print(*args, sep='\n')
        print("┌" + "─" * max_option_length + "┐")
        for opt in options:
            spaces_required = max_option_length - len(opt['text']) - 4
            print(f"│ {opt['option']}. {opt['text']}" + ' ' * spaces_required + "│")
        print("└" + "─" * max_option_length + "┘")
        
        choice = input('> ')
        action = next((opt['action'] for opt in options if opt['option'] == choice), None)
        
        
        if action:
            result = action()
            if result in ["back", "exit"]:
                print_header(username)
                return result
            return result
        else:
            print_header(username)
            print('Invalid choice')

def print_header(username=None):
    clear_screen()
    header =("##################")
    title = ("#   GOODCHAIN    #")

    if username:
        print("\nLogged in as: " + username + "\n")

    print(header)
    print(title)
    print(header)
    print("")

def load_private_key_from_string(private_key_string):
    private_key_bytes = private_key_string.encode("utf-8")
    private_key = serialization.load_pem_private_key(
        private_key_bytes,
        password=None,
    )
    return private_key

def get_current_user_public_key(username):
    db = Database()
    if not username:
        return None

    user_data = db.fetch('SELECT publickey FROM users WHERE username=?', (username, ))
    if user_data:
        return user_data[0][0]
    return None


def sign(message, private_key):
    message = bytes(str(message), 'utf-8')
    signature = private_key.sign(
        message,
        ec.ECDSA(hashes.SHA256())
        )
    return signature

def verify(message, signature, pbc_ser):
    message = bytes(str(message), 'utf-8')
    public_key = serialization.load_pem_public_key(pbc_ser)
    try:
        public_key.verify(
            signature,
            message,
            ec.ECDSA(hashes.SHA256())
            )
        return True
    except InvalidSignature:
         return False
    except:
        print("Error executing 'public_key.verify'")
        return False