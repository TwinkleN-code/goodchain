import sqlite3
import re
import getpass
import bcrypt
from utils import print_header
from database import Database
from transaction import transaction_pool, Transaction, REWARD
from storage import save_to_file, load_from_file

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

        password = password.encode('utf-8')
        hashed_pw = bcrypt.hashpw(password, bcrypt.gensalt())

        try:
            self.db.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, hashed_pw))
            print_header(username)
            print('Registration successful')
            self.current_user = username
            self.reward_user()
        except sqlite3.Error as e:
            print_header()
            print(f"Database error: {e}")

    def login(self):
        username = input('Enter your username: ').lower()
        password = getpass.getpass('Enter your password: ').encode('utf-8')

        retrieved_user =self.db.fetch('SELECT password FROM users WHERE username=?', (username, ))

        if retrieved_user and bcrypt.checkpw(password, retrieved_user[0][0]):
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

        if self.username_exists(new_username):
            print_header(self.current_user)
            print('Username is already taken')
            return
        
        if not self.validate_username(new_username):
            print_header(self.current_user)
            print('Username must be between 3 and 32 characters and contain only letters and numbers')
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
        
        new_password = new_password.encode('utf-8')
        
        retrieved_user =self.db.fetch('SELECT password FROM users WHERE username=?', (self.current_user, ))

        if retrieved_user and bcrypt.checkpw(new_password, retrieved_user[0][0]):
            print_header(self.current_user)
            print('New password cannot be the same as the old password')
            return
        
        confirm_password = getpass.getpass('Confirm password: ').encode('utf-8')

        while new_password != confirm_password:
            print_header(self.current_user)
            print('Passwords do not match')
            return
        
        hashed_pw = bcrypt.hashpw(new_password, bcrypt.gensalt())

        try: 
            self.db.execute('UPDATE users SET password=? WHERE username=?', (hashed_pw, self.current_user))
            print_header(self.current_user)
            print('Password successfully changed')
        except sqlite3.Error as e:
            print_header(self.current_user)
            print(f"Database error: {e}")

    def reward_user(self):
        initial_transaction = Transaction(REWARD)
        initial_transaction.add_output(self.current_user, 50)
        transaction_pool.add_transaction(initial_transaction)

    def view_balance(self):
        transactions = load_from_file()
        user_balance = self.calculate_balance(self.current_user, transactions)
        print_header(self.current_user)
        print(f"Balance for {self.current_user}: {user_balance} coins.")

    def calculate_balance(self, user, transactions):
        balance = 0
        for tx in transactions:
            for output_addr, tx_amount in tx.outputs:
                if output_addr == user:
                    balance += tx_amount
            for input_addr, tx_amount in tx.inputs:
                if input_addr == user:
                    balance -= tx_amount
        return balance
    
    def view_transactions(self):
        transactions = load_from_file()

        if not transactions:
            print_header(self.current_user)
            print("No transactions found.")
        else:
            print_header(self.current_user)
            print("All Transactions:")
            for tx in transactions:
                print(tx)

    def delete_account(self):
        confirm = input('Are you sure you want to delete your account? (y/n) ')

        if confirm == 'y':
            try:
                self.db.execute('DELETE FROM users WHERE username=?', (self.current_user, ))
                print_header()
                print('Account successfully deleted')
                self.current_user = None
            except sqlite3.Error as e:
                print_header(self.current_user)
                print(f"Database error: {e}")
        else:
            print_header(self.current_user)
            print('Account deletion cancelled')

    # def send_coins(self):
    #     recipient = input('Enter the recipient: ').lower()
    #     amount = input('Enter the amount: ')

    #     try:
    #         amount = int(amount)
    #     except ValueError:
    #         print_header(self.current_user)
    #         print('Invalid amount')
    #         return

    #     if amount <= 0:
    #         print_header(self.current_user)
    #         print('Invalid amount')
    #         return

    #     if recipient == self.current_user:
    #         print_header(self.current_user)
    #         print("You can't send coins to yourself")
    #         return

    #     balance = 0
    #     for tx in transaction_pool.get_transactions():
    #         for output_addr, tx_amount in tx.outputs:
    #             if output_addr == self.current_user:
    #                 balance += tx_amount
    #         for input_addr, tx_amount in tx.inputs:
    #             if input_addr == self.current_user:
    #                 balance -= tx_amount
        
    #     if balance < amount:
    #         print_header(self.current_user)
    #         print('Insufficient funds')
    #         return

    #     transaction = Transaction()
    #     transaction.add_input(self.current_user, amount)
    #     transaction.add_output(recipient, amount)
    #     transaction.sign(self.current_user)
    #     transaction_pool.add_transaction(transaction)

    #     print_header(self.current_user)
    #     print('Transaction successful')