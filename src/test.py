import hashlib
import pickle
import sqlite3
from auth import PEPPER, User
from recover_key import generate_random_mnemonic
from transaction import REWARD, REWARD_VALUE, Transaction, TransactionPool, transaction_pool
from keys import encrypt_private_key, fetch_decrypted_private_key, generate_keys, read_key
from utils import *
import os


# function that automatic adds transactions for testing
# FIRST CREATE 2 ACOUNTS
def automatic_transactions(sender, receiver):
    amount_to_transfer = 2
    transaction_fee = 0.5

    transaction = Transaction(0, transaction_fee)
    private_key = fetch_decrypted_private_key(sender)
    public_key_receiver = get_current_user_public_key(receiver)
    public_key = get_current_user_public_key(sender)
    transaction.add_input(public_key, amount_to_transfer)
    transaction.add_output(public_key_receiver,amount_to_transfer)
    transaction.sign(private_key)
    # add to the pool
    transaction_pool = TransactionPool()
    transaction_pool.add_transaction(transaction)
    print('Automatic transactions successful')

def automatic_accounts(username, password):
    hashed_pw = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            PEPPER,
            iterations=100000,
            dklen=128
        )

    # create keys
    user_private_key, user_public_key = generate_keys()
    database_key = read_key()
    if database_key != "":
        encrypted_private_key = encrypt_private_key(database_key, user_private_key)
    else: return

    # create mnemonic phrase
    phrase = generate_random_mnemonic()
    hashed_phrase = hashlib.sha256(phrase.encode()).hexdigest()

    # save to db
    db = Database()
    try:
        db.execute('INSERT INTO users (username, password, privatekey, publickey, phrase) VALUES (?, ?, ?, ?, ?)', (username, hashed_pw, encrypted_private_key, user_public_key, hashed_phrase))
    except sqlite3.Error as e:
        print_header()
        print(f"Database error: {e}")
        return
    
    # reward user
    decrypted_private_key = fetch_decrypted_private_key(username)
    public_key = get_current_user_public_key(username)
    reward_transaction = Transaction(type=REWARD)

    # Since it's a reward, there are no inputs.
    reward_transaction.add_output(public_key, REWARD_VALUE)
    reward_transaction.sign(decrypted_private_key)

    transaction_pool.add_transaction(reward_transaction)

    print('\nRegistration successful')


def make_invalid_transaction(sender, receiver):
    amount_to_transfer = 4
    transaction_fee = 0.4

    transaction = Transaction(0, transaction_fee)
    #private_key = fetch_decrypted_private_key(sender)
    public_key_receiver = get_current_user_public_key(receiver)
    public_key = get_current_user_public_key(sender)
    transaction.add_input(public_key, amount_to_transfer)
    transaction.add_output(public_key_receiver,amount_to_transfer)
    private_key_player = fetch_decrypted_private_key("test2") #invalid transaction
    transaction.sign(private_key_player)
    # add to the pool
    transaction_pool.add_transaction(transaction)
    print('Invalid transactions made')

db = Database()
db.setup()
if not os.path.isfile('blockchain.dat'):
    data = []
    with open("blockchain.dat", 'wb') as file:
        pickle.dump(data, file)
if not os.path.isfile('transactions.dat'):
    with open("transactions.dat", "w"):
        pass

#make 7 accounts 
# automatic_accounts("admin", "Admin123!")
# automatic_accounts("test", "Test123!")
# j = 1
# while j <= 5:
#     automatic_accounts("test" + str(j), "Test123!")
#     j += 1



# make_invalid_transaction('admin', 'test')


