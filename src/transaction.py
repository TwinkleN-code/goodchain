from notifications import notification
from database import Database
from miner_client import send_data_to_miner_servers, data_type_miner
from utils import BLOCK_STATUS, calculate_balance, calculate_pending_balance, get_current_user_public_key, remove_from_file, sign, verify, print_header, get_all_transactions, display_menu_and_get_choice
from storage import save_to_file, load_from_file, transactions_file_path, blockchain_file_path
import time
from wallet_client import send_data_to_miner_servers

REWARD_VALUE = 50
NORMAL = 0
REWARD = 1

class TransactionPool:
    def __init__(self):
        self.transactions = []

    def add_transaction(self, transaction, filename):
        self.transactions.append(transaction)
        self._save_transaction_to_file(transaction, filename)
    
    def _save_transaction_to_file(self, transaction, filename):
        transactions = load_from_file(filename)
        transactions.append(transaction)
        save_to_file(transactions, filename)

transaction_pool = TransactionPool()

class Transaction:
    def __init__(self, type = NORMAL, fee=0):
        self.timestamp = time.time()
        self.type = type
        self.input = None
        self.output = None
        self.sig = None
        self.fee = fee
        self.validators = []

    def add_input(self, from_addr, amount):
        self.input = (from_addr, amount)

    def add_output(self, to_addr, amount):
        self.output = (to_addr, amount)

    def sign(self, private):
        message = self._prepare_data_for_signature()
        self.sig = sign(message, private)
    
    def _has_valid_signature(self, message, addr):
        return verify(message, self.sig, addr)
               
    def is_valid(self):
        if self.type == REWARD:
            if self.input is not None or self.output is None:
                return False
            if not self._has_valid_signature(self._prepare_data_for_signature(), self.output[0]):
                return False
            return True
        
        if self.input is None or self.output is None:
            return False
        
        total_in = self.input[1] if self.input[1] >= 0 else 0
        total_out = self.output[1] if self.output[1] >= 0 else 0

        # Ensure that the sum of inputs matches the sum of outputs
        if total_out != total_in:
            return False
        
        # Check if the signature is valid for the given input address
        if not self._has_valid_signature(self._prepare_data_for_signature(), self.input[0]):
            return False
        
        # check if enough balance
        chain = load_from_file(blockchain_file_path)
        pool_transactions = load_from_file(transactions_file_path)
        available_balance = 0
        pending_balance = 0
        for block in chain:
            if block.status == BLOCK_STATUS[1] and block.transactions[-1].output[0] == self.input[0]:
                available_balance += calculate_balance(self.input[0], block.transactions, True)
            elif block.status == BLOCK_STATUS[1]:
                available_balance += calculate_balance(self.input[0], block.transactions)
            elif block.status == BLOCK_STATUS[0]:
                pending_balance += calculate_pending_balance(self.input[0], block.transactions)

        if pool_transactions:
            pending_balance += calculate_pending_balance(self.input[0],pool_transactions)

        if (self.input[1] + self.fee) > (available_balance - pending_balance):
            return False

        return True

    def _prepare_data_for_signature(self):
        return [self.input, self.output, self.fee]

    def view_transactions(self, username):
        transactions = get_all_transactions(transactions_file_path)
        options = [
        {"option": "1", "text": "Back to main menu", "action": lambda: "back"}
        ]

        if not transactions:
            print_header(username)
            print("No transactions found.")
        else:
            print_header(username)
            transactions_to_display = "All Transactions: \n\n"
            for tx in transactions:
                if len(tx) == 8:
                    if len(tx[7]) > 0: #if there are invalid flags in the transaction
                        names = ", ".join([name for name, _ in tx[7]]) if len(tx[7]) > 1 else tx[7][0][0]
                        transactions_to_display += f"Normal Transaction: {tx[1]} coin(s) sent from {tx[3]} to {tx[2]} including a transaction fee of {tx[4]} coin(s). \n ↳ flagged invalid by: {names}\n"
                    elif tx[4] == 0 and len(tx[7]) == 0: # fee transaction
                        transactions_to_display += f"Transaction Fee: {tx[1]} coin(s) sent from {tx[3]} to {tx[2]}\n"
                    elif tx[4] == 0 and len(tx[7]) != 0: # invalid fee transaction
                        names = ", ".join([name for name, _ in tx[7]]) if len(tx[7]) > 1 else tx[7][0][0]
                        transactions_to_display += f"Transaction Fee: {tx[1]} coin(s) sent from {tx[3]} to {tx[2]}\n ↳ flagged invalid by: {names}\n"
                    else:
                        transactions_to_display += f"Normal Transaction: {tx[1]} coin(s) sent from {tx[3]} to {tx[2]} including a transaction fee of {tx[4]} coin(s)\n"
                else:
                    if len(tx[5]) > 0:
                        names = ", ".join([name for name, _ in tx[5]]) if len(tx[5]) > 1 else tx[5][0][0]
                        transactions_to_display += f"Reward Transaction: {tx[1]} coins credited to {tx[2]}\n ↳ flagged invalid by: {names}\n"
                    else:
                        transactions_to_display += f"Reward Transaction: {tx[1]} coins credited to {tx[2]}\n"
            
            display_menu_and_get_choice(options, username, transactions_to_display)

    def __repr__(self):
        types_str = "Reward transaction" if self.type == REWARD else "Normal transaction"
        if self.input:
            inputs_str = f"{self.input[1]} from {self.input[0]}" if self.input else ""
        else:
            inputs_str = "No input"
        outputs_str = f"{self.output[1]} to {self.output[0]}" if self.output else ""
        
        return (f"TYPE:\n{types_str}\n"
                f"INPUT:\n{inputs_str}\n"
                f"OUTPUT:\n{outputs_str}\n"
                f"TRANSACTION FEE:\n{self.fee}\n"
                f"SIGNATURE:\n{self.sig}\n"
                f"END\n")
    
def cancel_invalid_transactions(username):
    db = Database()
    pool_transactions = load_from_file(transactions_file_path)
    public_key = get_current_user_public_key(username)
    
    if pool_transactions:
        for tx in reversed(pool_transactions):
            if tx.input:
                if tx.input[0] == public_key:
                    if len(tx.validators) > 0:
                        index = pool_transactions.index(tx)
                        # delete from pool
                        remove_from_file(transactions_file_path, index)
                        # send to servers
                        send_data_to_miner_servers((data_type_miner[2], index)) 
                        #notify user
                        receiver = db.fetch('SELECT username FROM users WHERE publickey=?', (tx.output[0], ))
                        if receiver:
                            notification.add_notification(username, f"rejected transaction: send {tx.input[1]} coin(s) to {receiver[0][0]} including transaction fee of {tx.fee} coins")                
            elif tx.input == None: # if there is an invalid reward transaction
                if tx.output[0] == public_key:
                    if len(tx.validators) > 0:
                        remove_from_file(transactions_file_path, index)
                        send_data_to_miner_servers((data_type_miner[2], index))
                        receiver = db.fetch('SELECT username FROM users WHERE publickey=?', (tx.output[0], ))
                        notification.add_notification(username, f"reward of {tx.input[1]} coin(s) rejected")   
            
            