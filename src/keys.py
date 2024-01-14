import os
import sqlite3
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec
from database import Database
from cryptography.fernet import Fernet
from utils import print_header, display_menu_and_get_choice, load_private_key_from_string

key_file_path = os.path.join("data", 'key.txt')

def set_key_file():
    if not os.path.isfile(key_file_path):
        key = generate_key()
        save_key(key, key_file_path)

def generate_keys():
    private_key = ec.generate_private_key(ec.SECP384R1())
    public_key = private_key.public_key()

    pbc_ser = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo)
    
    pr_ser = private_key.private_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PrivateFormat.PKCS8,
    encryption_algorithm=serialization.NoEncryption())

    return pr_ser, pbc_ser


def encrypt(message, key):
    try:
        fernet = Fernet(key)
        encrypted_message = fernet.encrypt(message.encode())
        return encrypted_message
    except Exception as e:
        print("Exception: " + str(e))
        return ""

def decrypt(encrypted_message, key):
    try:
        fernet = Fernet(key)
        decrypted_message = fernet.decrypt(encrypted_message).decode()
        return decrypted_message
    except Exception as e:
        print("Exception: " + str(e))
        return ""
    
def view_user_keys(username):
    db = Database()
    print_header(username)

    # get public key 
    try:
        get_pb = db.fetch('SELECT publickey FROM users WHERE username=?', (username, ))
    except sqlite3.Error as e:
            print_header(username)
            print(f"Database error: {e}")

    get_pb = get_pb[0][0]
    if isinstance(get_pb, bytes):
        get_pb = get_pb.decode('utf-8')
    cleaned_public_key = get_pb.replace("-----BEGIN PUBLIC KEY-----", "").replace("-----END PUBLIC KEY-----", "").strip()
    public_key = f"\nPublic Key: \n{cleaned_public_key} \n"

    # get private key and decrypt it
    try:
        get_pr = db.fetch('SELECT privatekey FROM users WHERE username=?', (username, ))
    except sqlite3.Error as e:
            print_header(username)
            print(f"Database error: {e}")

    db_key = read_key()
    if db_key != "":
        decrypted = decrypt_private_key(db_key, get_pr[0][0])
        if isinstance(decrypted, bytes):
            decrypted = decrypted.decode('utf-8')
        cleaned_private_key = decrypted.replace("-----BEGIN PRIVATE KEY-----", "").replace("-----END PRIVATE KEY-----", "").strip()
        private_key = f"Private Key: \n{cleaned_private_key}"
    else:
        print("Key not found")

    options = [{"option": "1", "text": "Back to main menu", "action": lambda: "back"}]
    choice_result = display_menu_and_get_choice(options, username, public_key, private_key)
    if choice_result == "back":
        return

def fetch_decrypted_private_key(username):
    """
    Fetches and decrypts the private key for the given username from the database.
    
    Parameters:
    - username (str): The username for which the private key should be fetched.
    
    Returns:
    - str: Decrypted private key for the provided username.
    """
    # Initialize database connection
    db = Database()

    # Fetch encrypted private key from database
    try:
        result = db.fetch('SELECT privatekey FROM users WHERE username=?', (username, ))
        if not result or len(result) == 0:
            print(f"No private key found for username: {username}")
            return None
        encrypted_private_key = result[0][0]
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return None

    # Read the decryption key from file
    db_key = read_key()
    if db_key == "":
        print("Decryption key not found")
        return None

    # Decrypt the private key
    decrypted_private_key = decrypt_private_key(db_key, encrypted_private_key)

    serialised_private_key = load_private_key_from_string(decrypted_private_key)

    return serialised_private_key

# generate a key to encrypt
def generate_key() : return Fernet.generate_key()

# save key to a file
def save_key(key, filename=key_file_path):
    key_string = key.decode("utf-8")
    try:
        with open(filename, "w") as key_file:
            key_file.write(key_string)
    except Exception as e:
        print("Exception: " + str(e))
        return ""
    
def read_key(filename=key_file_path):
    try:
        with open(filename, "r") as key_file:
            key_string = key_file.read()
            return key_string
    except Exception as e:
        print("Exception: " + str(e))
        return ""

def encrypt_private_key(encryption_key, private_key):
    if not isinstance(encryption_key, bytes):
        encryption_key = encryption_key.encode('utf-8')

    # Ensure private_key is in bytes format
    if not isinstance(private_key, bytes):
        private_key = private_key.encode('utf-8')
        
    key_object = Fernet(encryption_key)
    encrypted_private_key = key_object.encrypt(private_key)
    return encrypted_private_key

def decrypt_private_key(encryption_key, encrypted_private_key):
    if not isinstance(encryption_key, bytes):
            encryption_key = encryption_key.encode('utf-8')

    key_object = Fernet(encryption_key)
    private_key = key_object.decrypt(encrypted_private_key)
    return private_key.decode('utf-8')

set_key_file()