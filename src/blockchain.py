import time
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from transaction import REWARD_VALUE, REWARD, Transaction, transaction_pool
from keys import fetch_decrypted_private_key
from storage import load_from_file
from utils import get_current_user_public_key, print_header, remove_from_file

class Block:
    def __init__(self, transactions, previous_hash, nonce=0):
        self.timestamp = time.time()
        self.transactions = transactions
        self.previous_hash = previous_hash
        self.nonce = nonce
        self.hash = self.compute_hash()

    def compute_hash(self):
        digest = hashes.Hash(hashes.SHA256(), backend=default_backend())
        digest.update(bytes(str(self.timestamp) + str(self.transactions) + str(self.previous_hash) + str(self.nonce), 'utf8'))
        return digest.finalize().hex()

    def mine(self, difficulty):
        pattern = '0' * difficulty
        start_time = time.time()
        while self.hash[:difficulty] != pattern:
            self.nonce += 1
            self.hash = self.compute_hash()
        end_time = time.time()
        print(f"Block mined in {end_time - start_time} seconds.")


class Ledger:
    def __init__(self):
        self.chain = [self.create_genesis_block()]
        self.difficulty = 4  # This can be adjusted based on your desired mining difficulty.
        self.mining_reward = REWARD_VALUE  # This is the reward a miner gets for mining a block.

    def create_genesis_block(self):
        # A function to generate genesis block and append it to the chain.
        genesis_block = Block([], "0")
        return genesis_block

    def add_block(self, block):
        # A function to add the block to the blockchain after it's mined.
        self.chain.append(block)
        
    def is_valid(self, difficulty):
        # Check for genesis block
        if not self.blocks:
            return True

        # Genesis block validation
        first_block = self.blocks[0]
        if not first_block.previous_hash is None:
            print("Genesis block's previous hash is not None.")
            return False

        # Start with the last block and validate chain integrity
        for i in range(1, len(self.blocks)):
            current_block = self.blocks[i]
            previous_block = self.blocks[i - 1]

            # 1. Check the previous_hash of the current block
            if current_block.previous_hash != previous_block.compute_hash():
                print("Previous block hash doesn't match with stored previous hash value.")
                return False

            # 2. Check the hash of the current block
            if current_block.hash != current_block.compute_hash():
                print("Hash of the block is not valid.")
                return False


            # 3. Check if block's hash meets the difficulty requirement
            if not current_block.compute_hash()[:difficulty] == '0' * difficulty:
                print("Block's hash doesn't meet the difficulty requirements.")
                return False

            # 4. Validate all transactions in the block
            for transaction in current_block.transactions:
                if not transaction.is_valid():
                    print(f"Transaction {transaction} in block {i} is not valid.")
                    return False

        return True


    def mine_transactions(self, username):
        transactions = load_from_file()
        # We take the first 5-10 transactions from the pool
        if len(transactions) < 5:
            print_header(username)
            print("Not enough transactions to mine.")
            return

        # Add a reward transaction for the miner
        decrypted_private_key = fetch_decrypted_private_key(username)
        public_key = get_current_user_public_key(username)
        reward_transaction = Transaction(type = REWARD)
        # Since it's a reward, there are no inputs. 
        reward_transaction.add_output(public_key, REWARD_VALUE)
        reward_transaction.sign(decrypted_private_key)
        
        transaction_pool.add_transaction(reward_transaction)

        transactions = load_from_file()
        
        # Create a new block with the transactions and mine it
        new_block = Block(transactions, self.chain[-1].hash)
        new_block.mine(self.difficulty)

        print(f"Block mined with hash: {new_block.hash}")
        self.add_block(new_block)

        # Remove the mined transactions from the transaction pool
        remove_from_file(transaction_pool, transactions)