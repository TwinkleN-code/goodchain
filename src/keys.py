from cryptography.exceptions import *
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from database import Database
from cryptography.fernet import Fernet


def generate_keys():
    private_key = rsa.generate_private_key(public_exponent=65537,key_size=2048)
    public_key = private_key.public_key()

    pbc_ser = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo)
    
    pr_ser = private_key.private_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PrivateFormat.PKCS8,
    encryption_algorithm=serialization.NoEncryption()
    )

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
    except InvalidKey as e:
        print(f"Invalid key: {e}")
        return None
    except (ValueError, InvalidTag) as e:
        print(f"Value error or invalid tag: {e}")
        return None
    except Exception as e:
        print("Exception: " + str(e))
        return False

def decrypt(ciphertext, private_key):
    try:
        text = private_key.decrypt(ciphertext,
                            padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA256()),
                            algorithm=hashes.SHA256(), label=None))
        return text.decode('utf-8')
    except Exception as e:
        print("Exception: " + str(e))
        return False
    
def view_user_keys(username):
    db = Database()
    while True:

        # get public key 
        get_pb = db.fetch('SELECT publickey FROM users WHERE username=?', (username, ))
        get_pb = get_pb[0][0].decode('utf-8')
        print(f"\nPublic Key: \n{get_pb}")

        # get private key and decrypt it
        get_pr = db.fetch('SELECT privatekey FROM users WHERE username=?', (username, ))
        db_key = read_key()
        decrypted = decrypt_private_key(db_key, get_pr[0][0])
        print(f"Private Key: \n{str(decrypted)}")
        
        print("\n1. Return")
        choice = input('> ')

        if choice == "1":
            return
        else:
            print('\nInvalid choice')


# generate a key to encrypt
def generate_key() : return Fernet.generate_key()

# save key to a file
def save_key(key):
    key_string = key.decode("utf-8")

    try:
        with open("key.txt", "w") as key_file:
            key_file.write(key_string)
    except Exception as e:
        print("Exception: " + str(e))
        return False
    
def read_key():
    try:
        with open("key.txt", "r") as key_file:
            key_string = key_file.read()
            return key_string
    except Exception as e:
        print("Exception: " + str(e))
        return False
    
def encrypt_private_key(encryption_key, private_key):
    if not isinstance(encryption_key, bytes):
            encryption_key = encryption_key.encode('utf-8')

    key_object = Fernet(encryption_key)
    encrypted_private_key = key_object.encrypt(private_key)
    return encrypted_private_key

def decrypt_private_key(encryption_key, encrypted_private_key):
    if not isinstance(encryption_key, bytes):
            encryption_key = encryption_key.encode('utf-8')

    key_object = Fernet(encryption_key)
    private_key = key_object.decrypt(encrypted_private_key)
    return private_key.decode('utf-8')
