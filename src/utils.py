import os
from cryptography.exceptions import *
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec
from database import Database
from storage import load_from_file, save_to_file, blockchain_file_path, transactions_file_path

BLOCK_STATUS = ["pending", "verified", "rejected", "genesis"]

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def display_menu_and_get_choice(options , username=None, *args):
    """Display menu based on the provided options and get user's choice."""
    max_option_length = max(len(opt['text']) for opt in options)
    max_option_number_length = max(len(str(opt['option'])) for opt in options)
    total_length = max_option_length + max_option_number_length + 6

    while True:
        print(*args, sep='\n')
        print("┌" + "─" * (total_length - 2) + "┐")
        for opt in options:
            spaces_required = (total_length - 1) - len(opt['text']) - len(str(opt['option'])) - 4
            print(f"│ {opt['option']}. {opt['text']}" + ' ' * spaces_required + "│")
        print("└" + "─" * (total_length - 2) + "┘")
        
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
            if args:
                print('')

def print_header(username=None):
    clear_screen()
    header =("##################")
    title = ("#   GOODCHAIN    #")

    if username:
        print("\nLogged in as: " + username + "\n")
        view_balance(username)

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
    
def find_index_from_file(filename, input, public_key_sender, public_key_receiver, fee):
    # Load all data from the file
    all_data = load_from_file(filename)

    # Find the index of the data that contains the target_input
    index = 0
    for tx in all_data:
        if tx.type == 0 and tx.input[1] == input and tx.input[0] == public_key_sender and tx.output[0] == public_key_receiver and tx.fee == fee:
            return index
        index += 1
    return None

def find_index_from_file_by_public_key(filename, public_key):
    # Load all data from the file
    all_data = load_from_file(filename)

    # Find the index of the data that contains the target_input
    index = 0
    for tx in all_data:
        if tx.type == 1 and tx.output[0] == public_key:
            return index
        index += 1
    return None

def get_user_transactions(filename, current_user):
    public_key = get_current_user_public_key(current_user)
    all_data = load_from_file(filename)
    db = Database()
    user_transactions = []
    count=1
    for tx in all_data:
        if tx.type == 0:
            if tx.input[0] == public_key:
                get_username = db.fetch('SELECT username FROM users WHERE publickey=?', (tx.output[0], ))
                user_transactions.append([count, tx.input[1], get_username[0][0], tx.fee])
                count += 1

    return user_transactions

def get_all_transactions(filename):
    all_data = load_from_file(filename)
    db = Database()
    user_transactions = []
    count=1
    for tx in all_data:
        get_receiver_username = db.fetch('SELECT username FROM users WHERE publickey=?', (tx.output[0], ))
        if tx.type == 0:
            get_sender_username = db.fetch('SELECT username FROM users WHERE publickey=?', (tx.input[0], ))
            user_transactions.append([count, tx.input[1], get_receiver_username[0][0], get_sender_username[0][0], tx.fee, tx.type, tx.timestamp, tx.validators])
        else:
            user_transactions.append([count, tx.output[1], get_receiver_username[0][0], tx.type, tx.timestamp, tx.validators])
        count += 1

    return user_transactions

def get_all_transactions_in_block(chain, block_index):
    db = Database()
    user_transactions = []
    count=1
    for tx in chain[block_index].transactions:
        get_receiver_username = db.fetch('SELECT username FROM users WHERE publickey=?', (tx.output[0], ))
        if tx.type == 0:
            get_sender_username = db.fetch('SELECT username FROM users WHERE publickey=?', (tx.input[0], ))
            user_transactions.append([count, tx.input[1], get_receiver_username[0][0], get_sender_username[0][0], tx.fee, tx.type])
        else:
            user_transactions.append([count, tx.output[1], get_receiver_username[0][0], tx.type])
        count += 1

    return user_transactions

def get_block_miner(filename, index):
    all_data = load_from_file(filename)
    db = Database()
    get_miner_username = db.fetch('SELECT username FROM users WHERE publickey=?', (all_data[index].transactions[-1].output[0], ))
    return get_miner_username[0][0]

def remove_from_file(filename, index):
    # Load all data from the file
    all_data = load_from_file(filename)

    # Check if the index is valid
    if 0 <= index < len(all_data):
        # Delete the entry 
        del all_data[index]
        # Save the modified data back to the file
        save_to_file(all_data, filename)
        return True
    return False


def calculate_balance(public_key, transactions, include_fee=False):
    balance = 0
    for tx in transactions:
        if tx.output:
            output_addr, tx_amount = tx.output
            if output_addr == public_key:
                balance += tx_amount
        if tx.input:
            input_addr, tx_amount = tx.input
            if input_addr == public_key:
                balance -= tx_amount
                balance -=tx.fee
        if include_fee:
                balance += tx.fee
    return balance

def calculate_pending_balance(public_key, transactions):
    balance = 0
    for tx in transactions:
        if tx.input:
            input_addr, tx_amount = tx.input
            if input_addr == public_key:
                balance += tx_amount
                balance += tx.fee
            if tx.input:
                input_addr, tx_amount = tx.input
                if input_addr == public_key:
                    balance -= tx_amount
                    balance -=tx.fee

    return balance

def view_balance(username):
        pool_transactions = load_from_file(transactions_file_path)
        public_key = get_current_user_public_key(username)
        private_key = None

        #pending balance from pool
        pending_balance = 0
        if pool_transactions:
            pending_balance += calculate_pending_balance(public_key, pool_transactions)

        #balance from validated blocks
        chain = load_from_file(blockchain_file_path)
        transactions = load_from_file(transactions_file_path)
        available_balance = 0
        pending_balance += calculate_balance(public_key, transactions)
        for block in chain:
            #add transaction fee to the balance
            if block.status == BLOCK_STATUS[1] and block.transactions[-1].output[0] == public_key:
                available_balance += calculate_balance(public_key, block.transactions, True)
            elif block.status == BLOCK_STATUS[1]:
                available_balance += calculate_balance(public_key, block.transactions)
            elif block.status == BLOCK_STATUS[0]: # balance from pending blocks
                pending_balance += calculate_pending_balance(public_key, block.transactions)
        
        print(f"Validated balance: {available_balance} coins") 
        if pending_balance != 0: 
            pending_balance = available_balance + pending_balance
            print(f"Spendable balance: {pending_balance} coins")
        print("\n")