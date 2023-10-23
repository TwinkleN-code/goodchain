import sqlite3
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import ec, padding
from database import Database
from cryptography.fernet import Fernet
from utils import print_header, display_menu_and_get_choice


def generate_keys():
    private_key = ec.generate_private_key(ec.SECP384R1())
    public_key = private_key.public_key()

    pbc_ser = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo).decode("utf-8").replace("-----BEGIN PUBLIC KEY-----", "").replace("-----END PUBLIC KEY-----", "").strip()
    
    pr_ser = private_key.private_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PrivateFormat.PKCS8,
    encryption_algorithm=serialization.NoEncryption()).decode("utf-8").replace("-----BEGIN PRIVATE KEY-----", "").replace("-----END PRIVATE KEY-----", "").strip()

    return pr_ser, pbc_ser


def encrypt(message, public_key):
    try:
        #convert to bytes
        if not isinstance(message, bytes):
            message = message.encode('utf-8')

        ciphertext = public_key.encrypt(
            message, 
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(), 
                label=None
            )
        )
        return ciphertext
    except Exception as e:
        print("Exception: " + str(e))
        return ""

def decrypt(ciphertext, private_key):
    try:
        text = private_key.decrypt(ciphertext,
                            padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA256()),
                            algorithm=hashes.SHA256(), label=None))
        return text.decode('utf-8')
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
    public_key = f"\nPublic Key: \n{get_pb}"

    # get private key
    get_key = get_private_key(username)
    private_key = ""
    if get_key != "":
        private_key = f"Private Key: \n{str(get_key)}"
    else:
        print("Could not find key")

    options = [{"option": "1", "text": "Back to main menu", "action": lambda: "back"}]
    choice_result = display_menu_and_get_choice(options, username, public_key, private_key)
    if choice_result == "back":
        return

# get private key
def get_private_key(username):
    db = Database()
    try:
        get_pr = db.fetch('SELECT privatekey FROM users WHERE username=?', (username, ))
    except sqlite3.Error as e:
        print_header(username)
        print(f"Database error: {e}")

    db_key = read_key()
    if db_key != "":
        return decrypt_private_key(db_key, get_pr[0][0])
    else:
        return ""

# generate a key to encrypt
def generate_key() : return Fernet.generate_key()

# save key to a file
def save_key(key, filename="key.txt"):
    key_string = key.decode("utf-8")
    try:
        with open(filename, "w") as key_file:
            key_file.write(key_string)
    except Exception as e:
        print("Exception: " + str(e))
        return ""
    
def read_key(filename="key.txt"):
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
