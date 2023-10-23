import sqlite3
import re
import getpass
from keys import encrypt_private_key, generate_keys, get_private_key, read_key, fetch_decrypted_private_key
from recover_key import generate_random_mnemonic
from utils import display_menu_and_get_choice, print_header, get_current_user_public_key
from database import Database
from transaction import transaction_pool, Transaction, REWARD, REWARD_VALUE
from storage import load_from_file
import hashlib

PEPPER = b"MySecretPepperValue"

class User:

    db = Database()

    def __init__(self):
        self.current_user = None
    
    def validate_password(self, password):
        if 8 <= len(password) <= 32:
            if re.search('[a-z]', password) is not None:
                if re.search('[A-Z]', password) is not None:
                    if re.search('[0-9]', password) is not None:
                        if re.search('[^a-zA-Z0-9]', password) is not None:
                            return True
                        
    def validate_username(self, username):
        if 3 <= len(username) <= 32:
            if re.search('^[a-zA-Z0-9]+$', username) is not None:
                return True
                        
    def username_exists(self, username):
        results = self.db.fetch('SELECT username FROM users WHERE username=?', (username, ))
        return results
    
    def hash_password(self, password):
        key = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            PEPPER,
            iterations=100000,
            dklen=128
        )
        return key
    
    def verify_password(self, stored_password, password):
        new_key = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            PEPPER,
            iterations=100000,
            dklen=128
        )
        return stored_password == new_key
        

    def register(self):
        username = input('Enter a username: ').lower()

        if self.username_exists(username):
            print_header()
            print('Username is already taken')
            return
        
        if not self.validate_username(username):
            print_header()
            print('Username must be between 3 and 32 characters and contain only letters and numbers')
            return
        
        password = getpass.getpass('Enter a password: ')

        if not self.validate_password(password):
            print_header()
            print('Password must be between 8 and 32 characters and contain at least one lowercase letter, one uppercase letter, one number, and one special character')
            return
        
        confirm_password = getpass.getpass('Confirm password: ')

        while password != confirm_password:
            print_header()
            print('Passwords do not match')
            return

        hashed_pw = self.hash_password(password)

        # create keys
        user_private_key, user_public_key = generate_keys()
        database_key = read_key()
        if database_key != "":
            encrypted_private_key = encrypt_private_key(database_key, user_private_key)
        else: return

        # create mnemonic phrase
        phrase = generate_random_mnemonic()
        hashed_phrase = hashlib.sha256(phrase.encode()).hexdigest()
        
        try:
            self.db.execute('INSERT INTO users (username, password, privatekey, publickey, phrase) VALUES (?, ?, ?, ?, ?)', (username, hashed_pw, encrypted_private_key, user_public_key, hashed_phrase))              
        except sqlite3.Error as e:
            print_header()
            print(f"Database error: {e}")
            return
        
        # reward user
        self.current_user = username
        self.reward_user()
        print_header(username)
        
        print('\nRegistration successful')
        print("\n**Important: Keep Your Recovery Key Safe** \n- Write it down and keep it offline. \n- Use this phrase to recover your private key \n- Never share it. Losing it can lead to permanent loss of your funds.")
        print("\nRECOVERY KEY: " + phrase)

        options = [{"option": "1", "text": "Go to profile", "action": lambda: "profile"}]
        choice_result = display_menu_and_get_choice(options, username)

        if choice_result == "profile":
            print_header(username)
            return

    def login(self):
        username = input('Enter your username: ').lower()
        password = getpass.getpass('Enter your password: ')

        retrieved_user =self.db.fetch('SELECT password FROM users WHERE username=?', (username, ))

        if retrieved_user and self.verify_password(retrieved_user[0][0], password):
            print_header(username)
            print('Login successful')
            self.current_user = username
        else:
            print_header()
            print('Invalid username or password')
                

    def logout(self):
        print_header()
        print("You've been logged out")
        self.current_user = None

    def change_username(self):
        new_username = input('Enter a new username: ').lower()

        if not self.validate_username(new_username):
            print_header(self.current_user)
            print('Username must be between 3 and 32 characters and contain only letters and numbers')
            return
        
        if self.username_exists(new_username):
            print_header(self.current_user)
            print('Username is already taken')
            return
        
        try:
            self.db.execute('UPDATE users SET username=? WHERE username=?', (new_username, self.current_user))
            print_header(new_username)
            print('Username successfully changed')
            self.current_user = new_username
        except sqlite3.IntegrityError:
            print_header(self.current_user)
            print('Username is already taken')

    def change_password(self):        
        new_password = getpass.getpass('Enter a new password: ')

        if not self.validate_password(new_password):
            print_header(self.current_user)
            print('Password must be between 8 and 32 characters and contain at least one lowercase letter, one uppercase letter, one number, and one special character')
            return
        
        retrieved_user = self.db.fetch('SELECT password FROM users WHERE username=?', (self.current_user, ))

        if self.verify_password(retrieved_user[0][0], new_password):
            print_header(self.current_user)
            print('New password cannot be the same as the old password')
            return
        
        confirm_password = getpass.getpass('Confirm password: ')

        if new_password != confirm_password:
            print_header(self.current_user)
            print('Passwords do not match')
            return
        
        hashed_pw = self.hash_password(new_password)

        try: 
            self.db.execute('UPDATE users SET password=? WHERE username=?', (hashed_pw, self.current_user))
            print_header(self.current_user)
            print('Password successfully changed')
        except sqlite3.Error as e:
            print_header(self.current_user)
            print(f"Database error: {e}")
    
    def reward_user(self):
        decrypted_private_key = fetch_decrypted_private_key(self.current_user)
        public_key = get_current_user_public_key(self.current_user)
        reward_transaction = Transaction(type=REWARD)

        # Since it's a reward, there are no inputs. 
        reward_transaction.add_output(public_key, REWARD_VALUE)
        reward_transaction.sign(decrypted_private_key)

        transaction_pool.add_transaction(reward_transaction)

    def view_balance(self):
        transactions = load_from_file("transactions.dat")
        public_key = get_current_user_public_key(self.current_user)
        user_balance = self.calculate_balance(public_key, transactions)
        print_header(self.current_user)
        print(f"Balance for {self.current_user}: {user_balance} coins.")

    def calculate_balance(self, user, transactions):
        balance = 0
        for tx in transactions:
            if tx.output:
                output_addr, tx_amount = tx.output
                if output_addr == user:
                    balance += tx_amount
            if tx.input:
                input_addr, tx_amount = tx.input
                if input_addr == user:
                    balance -= tx_amount
        return balance
    
    def view_transactions(self):
        transactions = load_from_file("transactions.dat")

        if not transactions:
            print_header(self.current_user)
            print("No transactions found.")
        else:
            print_header(self.current_user)
            print("All Transactions: \n")
            for tx in transactions:
                print(tx)

    def transfer_coins(self):
        amount_to_transfer = input("Enter number of coins to send: ")
        receiver_username = input("Enter the receiver's username: ").replace(" ", "").lower()
        transaction_fee = input("Enter transaction fee: ")

        options = [{"option": "1", "text": "Confirm transaction", "action": lambda: "confirm"},
                {"option": "2", "text": "Back to main menu", "action": lambda: "back"}]
        choice_result = display_menu_and_get_choice(options)
        if choice_result == "back":
            return
        
        try: 
            amount_to_transfer = float(amount_to_transfer)
            transaction_fee = float(transaction_fee)
        except ValueError:
            print_header()
            print("Invalid input")
            return
        
        # check if username is current user
        if receiver_username == self.current_user:
            print_header()
            print("Cannot send coins to yourself")
            return
        
        # amount should be > 0
        if amount_to_transfer <= 0:
            print_header()
            print('Invalid amount')
            return
        
        # check if enough balance
        transactions = load_from_file()
        balance = self.calculate_balance(self.current_user, transactions)
        if balance < amount_to_transfer + transaction_fee:
            print_header()
            print("Insufficient balance")
            return

        # check if receiver exists
        if not self.username_exists(receiver_username):
            print_header()
            print('Receiver does not exists.')
            return
            
        # make the transaction
        transaction = Transaction()
        transaction.add_input(self.current_user, amount_to_transfer)
        transaction.add_output(receiver_username,amount_to_transfer)

        # sign transaction
        private_key = get_private_key(self.current_user)
        transaction.sign(private_key)

        # add to the pool
        transaction_pool.add_transaction(transaction)

        print_header(self.current_user)
        print('Transaction successful')