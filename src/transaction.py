from utils import sign, verify, print_header
from storage import save_to_file, load_from_file

REWARD_VALUE = 50
NORMAL = 0
REWARD = 1

class TransactionPool:
    def __init__(self):
        self.transactions = []

    def add_transaction(self, transaction):
        self.transactions.append(transaction)
        self._save_transaction_to_file(transaction)
    
    def _save_transaction_to_file(self, transaction):
        transactions = load_from_file("transactions.dat")
        transactions.append(transaction)
        save_to_file(transactions, "transactions.dat")

transaction_pool = TransactionPool()

class Transaction:
    def __init__(self, type = NORMAL, fee=0):
        
        self.type = type
        self.input = None
        self.output = None
        self.sig = None
        self.fee = fee

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

        return True

    def _prepare_data_for_signature(self):
        return [self.input, self.output, self.fee]

    def view_transactions(self, username):
        transactions = load_from_file("transactions.dat")

        if not transactions:
            print_header(username)
            print("No transactions found.")
        else:
            print_header(username)
            print("All Transactions: \n")
            for tx in transactions:
                print(tx)

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