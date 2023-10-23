
from utils import sign, verify
from storage import save_to_file, load_from_file

REWARD_VALUE = 50
NORMAL = 0
REWARD = 1

class TransactionPool:
    def __init__(self):
        self.transactions = []

    def add_transaction(self, transaction):
        self.transactions.append(transaction)
        self.save_transaction_to_file(transaction)

    def get_transactions(self):
        return self.transactions
    
    def save_transaction_to_file(self, transaction):
        transactions = load_from_file()
        transactions.append(transaction)
        save_to_file(transactions)

transaction_pool = TransactionPool()

class Transaction:
    def __init__(self, type = NORMAL):
        
        self.type = type
        self.inputs = []
        self.outputs = []
        self.sigs = []
        self.reqd = []

    def add_input(self, from_addr, amount):
        self.inputs.append((from_addr, amount))

    def add_output(self, to_addr, amount):
        self.outputs.append((to_addr, amount))

    def add_reqd(self, addr):
        self.reqd.append(addr)

    def sign(self, private):
        message = self.__gather()
        newsig = sign(message, private)
        self.sigs.append(newsig)
    
    def _has_valid_signature(self, message, addr):
        return any(verify(message, s, addr) for s in self.sigs)
               
    def is_valid(self):
        if self.type == REWARD:
            return len(self.inputs) == 0 and len(self.outputs) == 1
        
        total_in = sum(amt for _, amt in self.inputs if amt >= 0)
        total_out = sum(amt for _, amt in self.outputs if amt >= 0)

        if total_out > total_in:
            return False

        message = self._gather()
        for addr, _ in self.inputs + self.reqd:
            if not self._has_valid_signature(message, addr):
                return False

        return True

    def __gather(self):
        data=[]
        data.append(self.inputs)
        data.append(self.outputs)
        data.append(self.reqd)
        return data

    def __repr__(self):

        inputs_str = "\n".join(f"{amt} from {addr}" for addr, amt in self.inputs)
        outputs_str = "\n".join(f"{amt} to {addr}" for addr, amt in self.outputs)
        reqd_str = "\n".join(str(addr) for addr in self.reqd)
        sigs_str = "\n".join(str(sig) for sig in self.sigs)
        
        return (f"INPUTS:\n{inputs_str}"
                f"OUTPUTS:\n{outputs_str} \n"
                f"EXTRA REQUIRED SIGNATURES:\n{reqd_str}"
                f"SIGNATURES:\n{sigs_str}"
                f"END\n")
    



    