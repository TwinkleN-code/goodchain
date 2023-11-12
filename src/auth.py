import datetime
import sqlite3
import re
import getpass
from keys import encrypt_private_key, generate_keys, read_key, fetch_decrypted_private_key
from recover_key import generate_random_mnemonic
from block_validation import automatic_tasks
from utils import BLOCK_STATUS, calculate_pending_balance, display_menu_and_get_choice, get_user_transactions, print_header, get_current_user_public_key, find_index_from_file, remove_from_file ,calculate_balance
from database import Database
from transaction import transaction_pool, Transaction, REWARD, REWARD_VALUE
from storage import load_from_file, blockchain_file_path, transactions_file_path
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
        print_header()
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
        print_header()
        username = input('Enter your username: ').lower()
        password = getpass.getpass('Enter your password: ')

        retrieved_user =self.db.fetch('SELECT password FROM users WHERE username=?', (username, ))

        if retrieved_user and self.verify_password(retrieved_user[0][0], password):
            automatic_tasks(username)
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

    def transfer_coins(self):
        print_header(self.current_user)
        amount_to_transfer = input("Enter number of coins to send: ")
        receiver_username = input("Enter the receiver's username: ").replace(" ", "").lower()
        transaction_fee = input("Enter transaction fee: ")

        options = [{"option": "1", "text": "Confirm transaction", "action": lambda: "confirm"},
                {"option": "2", "text": "Cancel", "action": lambda: "back"}]
        try:
            amount_to_transfer = float(amount_to_transfer)
            transaction_fee = float(transaction_fee)
        except ValueError:
            print_header(self.current_user)
            print("Please enter a correct number")
            return

        # check if username is current user
        if receiver_username == self.current_user:
            print_header(self.current_user)
            print("Cannot send coins to yourself")
            return

        if amount_to_transfer <= 0 or transaction_fee <= 0:
            print_header(self.current_user)
            print('Invalid amount')
            return

        # check if enough balance [amount_to_transfer + transfer_fee <= available balance - (pending balance from pool + pending balance from blocks)]
        chain = load_from_file(blockchain_file_path)
        public_key = get_current_user_public_key(self.current_user)
        available_balance = 0
        pending_balance = 0
        for block in chain:
            if block.status == BLOCK_STATUS[1] and block.transactions[-1].output[0] == public_key:
                available_balance += calculate_balance(public_key, block.transactions, True)
            elif block.status == BLOCK_STATUS[1]:
                available_balance += calculate_balance(public_key, block.transactions)
            elif block.status == BLOCK_STATUS[0]: 
                pending_balance += calculate_pending_balance(public_key, block.transactions) 

        pool_transactions = load_from_file(transactions_file_path)
        if pool_transactions:
            pending_balance += calculate_pending_balance(public_key,pool_transactions)

        if (amount_to_transfer + transaction_fee) > (available_balance - pending_balance):
            print_header(self.current_user)
            print("Insufficient balance available")
            return
        
        # check if receiver exists
        if not self.validate_username(receiver_username):
            print_header(self.current_user)
            print("Invalid username")
            return

        if not self.username_exists(receiver_username):
            print_header(self.current_user)
            print('Receiver does not exists.')
            return
        
        print_header(self.current_user)
        choice_result = display_menu_and_get_choice(options, self.current_user, f"You are sending {amount_to_transfer} coins to {receiver_username} with {transaction_fee} transaction fee\n")
        if choice_result == "back":
            return

        # make the transaction
        transaction = Transaction(0, transaction_fee)
        private_key = fetch_decrypted_private_key(self.current_user)
        public_key_receiver = get_current_user_public_key(receiver_username)
        transaction.add_input(public_key, amount_to_transfer)
        transaction.add_output(public_key_receiver,amount_to_transfer)

        # sign transaction
        transaction.sign(private_key)

        # check if transaction is valid
        if not transaction.is_valid():
            print_header(self.current_user)
            print("Invalid transaction")
            return

        # add to the pool
        transaction_pool.add_transaction(transaction)

        print_header(self.current_user)
        print('Transaction successful')

    def remove_transaction(self):
        print_header(self.current_user)
        # show all user transactions from the pool
        transactions = get_user_transactions(transactions_file_path, self.current_user) # [number, input amount, username sender, fee]
        if transactions == []:
            print_header(self.current_user)
            print("You have no pending transactions")
            return
        
        print("Pending transactions:\n")
        for tx in transactions:
            print(f"{str(tx[0])}. {tx[1]} to {tx[2]} with {tx[3]} transaction fee")
        print(f"{len(transactions)+1}. Back to main menu\n")
        
        choice = input("Enter transaction to cancel: ")
        try:
            choice = int(choice)
        except ValueError:
            print_header(self.current_user)
            print("Please enter a correct number")
            return
        
        if choice == len(transactions)+1:
            print_header(self.current_user)
            return
        else:
            #confirm
            print_header(self.current_user)
            options = [{"option": "1", "text": "Delete transaction", "action": lambda: "confirm"},
                {"option": "2", "text": "Cancel", "action": lambda: "back"}]
            choice_result = display_menu_and_get_choice(options, self.current_user, f"You are deleting transaction: {transactions[choice-1][1]} to {transactions[choice-1][2]} with {transactions[choice-1][3]} transaction fee \n")
            if choice_result == "back":
                print_header(self.current_user)
                return
            
            # delete from pool
            index = find_index_from_file(transactions_file_path, transactions[choice-1][1], get_current_user_public_key(self.current_user), get_current_user_public_key(transactions[choice-1][2]), transactions[choice-1][3])
            remove = remove_from_file(transactions_file_path, index)
            if remove:
                print_header(self.current_user)
                print("Transaction canceled")
            else:
                print_header(self.current_user)
                print("Could not cancel transaction")
            return

    def edit_transaction(self):
        transactions = get_user_transactions(transactions_file_path, self.current_user) # [number, input amount, username sender, fee]
        if transactions == []:
            print_header(self.current_user)
            print("You have no pending transactions")
            return
        print_header(self.current_user)
        print("Pending transactions")
        for tx in transactions:
            print(f"{str(tx[0])}. {tx[1]} to {tx[2]} with {tx[3]} transaction fee")
        print(f"{len(transactions)+1}. Back to main menu")
        
        choice = input("Enter transaction to modify: ")
        try:
            choice = int(choice)
        except ValueError:
            print_header(self.current_user)
            print("Please enter a correct number")
            return
        if choice > len(transactions)+1 or choice < 1:
            print_header(self.current_user)
            print("Please enter a correct number")
            return
        if choice == len(transactions)+1:
            print_header(self.current_user)
            return
        else:
            print_header(self.current_user)
            self.transaction_edit_menu(transactions, choice-1)
            return

    def transaction_edit_menu(self, transactions, tx_choice):
        options = [
            {"option": "1", "text": "Edit amount of coins", "action": lambda: 1},
            {"option": "2", "text": "Edit receiver's username", "action": lambda: 2},
            {"option": "3", "text": "Edit transaction fee", "action": lambda: 3},
            {"option": "4", "text": "Back to menu", "action": lambda: "back"}]
        edit_choice = display_menu_and_get_choice(options, self.current_user, f"You are editing transaction: {transactions[tx_choice][1]} to {transactions[tx_choice][2]} with {transactions[tx_choice][3]} transaction fee")
        if edit_choice == "back":
            return
        else:
            tx = Transaction(0, transactions[tx_choice][3])
            private_key = fetch_decrypted_private_key(self.current_user)
            public_key = get_current_user_public_key(self.current_user)
            public_key_receiver = get_current_user_public_key(transactions[tx_choice][2])
            index = find_index_from_file(transactions_file_path, transactions[tx_choice][1],  public_key, public_key_receiver, transactions[tx_choice][3])
            if edit_choice == 2:
                new_username = input("Enter new username: ").replace(" ", "").lower()
                if not self.validate_username(new_username) or not self.username_exists(new_username):
                    print_header(self.current_user)
                    print("Invalid username")
                    return
                if new_username == transactions[tx_choice][2]:
                    print_header(self.current_user)
                    print("That's the same username")
                    return

                public_key_new_receiver = get_current_user_public_key(new_username)
                tx.add_input(public_key, transactions[tx_choice][1])
                tx.add_output(public_key_new_receiver, transactions[tx_choice][1])

            elif edit_choice == 3:
                new_fee = input("Enter new transaction fee: ")
                try:
                    new_fee = float(new_fee)
                except ValueError:
                    print_header(self.current_user)
                    print("Please enter a correct number")
                    return
                if new_fee <= 0:
                    print_header(self.current_user)
                    print('Invalid amount')
                    return
                if new_fee == transactions[tx_choice][3]:
                    print_header(self.current_user)
                    print("That's the same transaction fee")
                    return

                # check if enough balance
                chain = load_from_file(blockchain_file_path)
                pool_transactions = load_from_file(transactions_file_path)
                available_balance = 0
                pending_balance = 0
                temp_amount = transactions[tx_choice][1]
                del pool_transactions[index] # skip the editting transaction when calculating balance
                for block in chain:
                    if block.status == BLOCK_STATUS[1] and block.transactions[-1].output[0] == public_key:
                        available_balance += calculate_balance(public_key, block.transactions, True)
                    elif block.status == BLOCK_STATUS[1]:
                        available_balance += calculate_balance(public_key, block.transactions)
                    elif block.status == BLOCK_STATUS[0]: 
                        pending_balance += calculate_pending_balance(public_key, block.transactions)

                if pool_transactions:
                    pending_balance += calculate_pending_balance(public_key,pool_transactions)

                if (new_fee + temp_amount) > (available_balance - pending_balance):
                    print_header(self.current_user)
                    print("Insufficient balance")
                    return
              
                tx.fee = new_fee
                tx.add_input(public_key, transactions[tx_choice][1])
                tx.add_output(public_key_receiver,transactions[tx_choice][1])

            elif edit_choice == 1:
                new_amount = input("Enter new amount: ")
                try:
                    new_amount = float(new_amount)
                except ValueError:
                    print_header(self.current_user)
                    print("Please enter a correct number")
                    return
                if new_amount <= 0:
                    print_header(self.current_user)
                    print('Invalid amount')
                    return
                if new_amount == transactions[tx_choice][1]:
                    print_header(self.current_user)
                    print("That's the same amount")
                    return

                # check if enough balance
                chain = load_from_file(blockchain_file_path)
                pool_transactions = load_from_file(transactions_file_path)
                available_balance = 0
                pending_balance = 0
                temp_fee = transactions[tx_choice][3]
                temp_amount = transactions[tx_choice][1]
                del pool_transactions[index]  #exclude selected transaction
                for block in chain:
                    if block.status == BLOCK_STATUS[1] and block.transactions[-1].output[0] == public_key:
                        available_balance += calculate_balance(public_key, block.transactions, True)
                    elif block.status == BLOCK_STATUS[1]:
                        available_balance += calculate_balance(public_key, block.transactions)
                    elif block.status == BLOCK_STATUS[0]:
                        pending_balance += calculate_pending_balance(public_key, block.transactions)

                if pool_transactions:
                    pending_balance += calculate_pending_balance(public_key,pool_transactions)

                if (new_amount + temp_fee) > (available_balance - pending_balance):
                    print_header(self.current_user)
                    print("Insufficient balance")
                    return
        
                tx.add_input(public_key, new_amount)
                tx.add_output(public_key_receiver, new_amount)

            tx.sign(private_key)
            
            #confirm
            options = [{"option": "1", "text": "Save changes", "action": lambda: "confirm"},
                        {"option": "2", "text": "Cancel", "action": lambda: "back"}]
            choice_result = display_menu_and_get_choice(options, self.current_user)
            if choice_result == "back":
                return
            
            # remove old transaction
            remove = remove_from_file(transactions_file_path, index)

            # check validation after old one is removed
            if not tx.is_valid(): 
                print_header(self.current_user)
                print("Invalid transaction")
                return
            
            # add transaction
            if remove:
                transaction_pool.add_transaction(tx)
                print_header(self.current_user)
                print('Transaction modified successfully')
                return
            else:
                print_header(self.current_user)
                print('Could not modify transaction')
                return  
            
    def view_transaction_history(self):
        db = Database()
        transaction_pool = load_from_file(transactions_file_path)
        chain = load_from_file(blockchain_file_path)
        public_key = get_current_user_public_key(self.current_user)
        options = [
        {"option": "1", "text": "Back to main menu", "action": lambda: "back"}
        ]

        transactions_to_display = ""
        pending_transactions_to_display = "Pending Transactions: \n"
        count_pending = 1
        count_val = 1

        for tx in transaction_pool:
            if tx.type == 0:
                if tx.input[0] == public_key:
                    get_receiver_username = db.fetch('SELECT username FROM users WHERE publickey=?', (tx.output[0], ))
                    pending_transactions_to_display += f"{count_pending}. {datetime.datetime.fromtimestamp(tx.timestamp).strftime('%d-%m-%Y %H:%M:%S')} Sending: {tx.input[1]} coin(s) to {get_receiver_username[0][0]} including transaction fee of {tx.fee} coin(s)\n"
                    count_pending += 1
                elif tx.output[0] == public_key:
                    get_sender_username = db.fetch('SELECT username FROM users WHERE publickey=?', (tx.input[0], ))
                    pending_transactions_to_display += f"{count_pending}. {datetime.datetime.fromtimestamp(tx.timestamp).strftime('%d-%m-%Y %H:%M:%S')} Receiving: {tx.output[1]} coin(s) from {get_sender_username[0][0]} including transaction fee of {tx.fee} coin(s)\n"
                    count_pending += 1
            else:
                if tx.output[0] == public_key:
                    pending_transactions_to_display += f"{count_pending}. {datetime.datetime.fromtimestamp(tx.timestamp).strftime('%d-%m-%Y %H:%M:%S')} Receiving reward: {tx.output[1]} coin(s)\n"
                    count_pending += 1

        validated_transactions_to_display = "\nVerified Transactions: \n"
        for block in chain:
            # transactions from pending blocks
            if block.status == BLOCK_STATUS[0]:
                for tx in block.transactions:
                    if tx.type == 0:
                        if tx.input[0] == public_key:
                            get_receiver_username = db.fetch('SELECT username FROM users WHERE publickey=?', (tx.output[0], ))
                            pending_transactions_to_display += f"{count_pending}. {datetime.datetime.fromtimestamp(tx.timestamp).strftime('%d-%m-%Y %H:%M:%S')} Sending: {tx.input[1]} coin(s) to {get_receiver_username[0][0]} including transaction fee of {tx.fee} coin(s)\n"
                            count_pending += 1
                        elif tx.output[0] == public_key:
                            get_sender_username = db.fetch('SELECT username FROM users WHERE publickey=?', (tx.input[0], ))
                            pending_transactions_to_display += f"{count_pending}. {datetime.datetime.fromtimestamp(tx.timestamp).strftime('%d-%m-%Y %H:%M:%S')} Receiving: {tx.output[1]} coin(s) from {get_sender_username[0][0]} including transaction fee of {tx.fee} coin(s)\n"
                            count_pending += 1
                    else:
                        if tx.output[0] == public_key:
                            pending_transactions_to_display += f"{count_pending}. {datetime.datetime.fromtimestamp(tx.timestamp).strftime('%d-%m-%Y %H:%M:%S')} Receiving reward: {tx.output[1]} coin(s)\n"
                            count_pending += 1
            # transactions from valid blocks
            elif block.status == BLOCK_STATUS[1]:
                for tx in block.transactions:
                    if tx.type == 0:
                        if tx.input[0] == public_key:
                            get_receiver_username = db.fetch('SELECT username FROM users WHERE publickey=?', (tx.output[0], ))
                            validated_transactions_to_display += f"{count_val}. {datetime.datetime.fromtimestamp(tx.timestamp).strftime('%d-%m-%Y %H:%M:%S')} Sending: {tx.input[1]} coin(s) to {get_receiver_username[0][0]} including transaction fee of {tx.fee} coin(s)\n"
                            count_val += 1
                        elif tx.output[0] == public_key:
                            get_sender_username = db.fetch('SELECT username FROM users WHERE publickey=?', (tx.input[0], ))
                            validated_transactions_to_display += f"{count_val}. {datetime.datetime.fromtimestamp(tx.timestamp).strftime('%d-%m-%Y %H:%M:%S')} Receiving: {tx.output[1]} coin(s) from {get_sender_username[0][0]} including transaction fee of {tx.fee} coin(s)\n"
                            count_val += 1
                    else:
                        if tx.output[0] == public_key:
                            validated_transactions_to_display += f"{count_val}. {datetime.datetime.fromtimestamp(tx.timestamp).strftime('%d-%m-%Y %H:%M:%S')} Receiving reward: {tx.output[1]} coin(s)\n"
                            count_val += 1

        if count_pending == 1:
            print_header(self.current_user)
            transactions_to_display += "You have no pending transactions \n"
        else:
            transactions_to_display += pending_transactions_to_display

        if count_val == 1:
            print_header(self.current_user)
            transactions_to_display += "You have no verified transactions \n"
        else:
            transactions_to_display += validated_transactions_to_display

        choice_result = display_menu_and_get_choice(options, self.current_user, transactions_to_display)
        if choice_result == "back":
            print_header(self.current_user)
            return