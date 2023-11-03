import time
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from block_validation import last_block_status
from transaction import REWARD_VALUE, REWARD, Transaction, NORMAL
from keys import fetch_decrypted_private_key
from storage import load_from_file, save_to_file
from utils import *
import os
import datetime

DIFFICULTY = 5
class Block:
    def __init__(self, transactions, previous_hash, block_id, nonce=0):
        self.id = block_id
        self.timestamp = time.time()
        self.transactions = transactions
        self.previous_hash = previous_hash
        self.nonce = nonce
        self.hash = None
        self.validators = []
        self.status = BLOCK_STATUS[0]
        # self.created_by = username

    def compute_hash(self):
        digest = hashes.Hash(hashes.SHA256(), backend=default_backend())
        digest.update(bytes(str(self.timestamp) + str(self.transactions) + str(self.previous_hash) + str(self.nonce), 'utf8'))
        return digest.finalize().hex()

    def mine(self, difficulty, username):
        print_header(username)
        print(f"Mining...")
        pattern = '0' * difficulty
        start_time = time.time()
        while True:
            self.hash = self.compute_hash()
            if self.hash[:difficulty] == pattern:
                break
            self.nonce += 1
        end_time = time.time()
        print_header(username)
        print(f"Block mined in {end_time - start_time:.0f} seconds.")

    def is_valid(self, previousBlock, username):
        #if block is genesis
        if self.previous_hash == "0" and id == 0:
            return True
        
        #check if transactions are valid
        invalid_tx = False
        for tx in self.transactions:
            if not tx.is_valid():
                tx.validators.append((username, "invalid"))
                invalid_tx = True

        if invalid_tx:
            return False
        
        #check the hash of the current block
        if self.hash != self.compute_hash():
            return False

        #check if block's hash meets the difficulty requirement
        if not self.hash[:DIFFICULTY] == '0' * DIFFICULTY:
            return False
        
        # if previous block is genesis
        if self.previous_hash == None and previousBlock.id == 0 and previousBlock.previous_hash == "0":
            return True
                
        return self.previous_hash == previousBlock.compute_hash()

    def __repr__(self):
        return f"Block(\n\tid: {self.id}, \n\ttimestamp: {self.timestamp}, \n\ttransactions: {self.transactions}, \n\tprevious_hash: {self.previous_hash}, \n\tnonce: {self.nonce}, \n\thash: {self.hash}\n)"


class Blockchain:
    def __init__(self):
        self.chain = [self.create_genesis_block()]
        self.difficulty = DIFFICULTY  # This can be adjusted based on your desired mining difficulty.
        self.mining_reward = REWARD_VALUE  # This is the reward a miner gets for mining a block.
        self.last_mined_timestamp = self._load_last_mined_timestamp() # This is the timestamp of the last mined block.

    def create_genesis_block(self):
        # A function to generate genesis block and append it to the chain.
        genesis_block = Block([], "0", 0)
        genesis_block.status = BLOCK_STATUS[1]
        return genesis_block
    
    def next_block_id(self):
        return len(self.chain)

    def add_block(self, block):
        # A function to add the block to the blockchain after it's mined.
        self.chain.append(block)
        self._save_block_to_file(block)

    def _save_block_to_file(self, block):
        blocks = load_from_file("blockchain.dat")
        if len(blocks) > 0: 
            blocks.append(block)
        else:
            blocks = self.chain
        save_to_file(blocks, "blockchain.dat")
        save_to_file(self.last_mined_timestamp, "last_mined_timestamp.dat")

    def _load_last_mined_timestamp(self):
        # Check if the file exists
        if os.path.exists("last_mined_timestamp.dat"):
            # Load the last mined timestamp from the file
            return load_from_file("last_mined_timestamp.dat")[0]
        else:
            # If the file does not exist, return a default value of 0
            return 0
        
    def is_valid(self):
        # Check for genesis block
        if not self.chain:
            return True
        
        previous_hash = "0"

        # Start with the last block and validate chain integrity
        for i, current_block in enumerate(self.chain):
            current_hash = current_block.compute_hash()

            # Skip genesis block but check its previous hash
            if i == 0:
                if current_block.previous_hash != "0":
                    print("Genesis block's previous hash should be '0'.")
                    return False
                continue

            # 1. Check the previous_hash of the current block
            if current_block.previous_hash != previous_hash:
                print("Previous block hash doesn't match with stored previous hash value.")
                return False

            # 2. Check the hash of the current block
            if current_block.hash != current_hash:
                print("Hash of the block is not valid.")
                return False


            # 3. Check if block's hash meets the difficulty requirement
            if not current_hash[:self.difficulty] == '0' * self.difficulty:
                print("Block's hash doesn't meet the difficulty requirements.")
                return False

            # 4. Validate all transactions in the block
            for transaction in current_block.transactions:
                if not transaction.is_valid():
                    print(f"Transaction {transaction} in block {i} is not valid.")
                    return False
                
            previous_hash = current_hash

        return True

    def mine_transactions(self, username):
        # add 3 minutes time interval
        current_timestamp = time.time()
        time_since_last_mine = current_timestamp - self.last_mined_timestamp
        if time_since_last_mine < 180:  # 180 seconds = 3 minutes
            print_header(username)
            print(f"Too soon to mine again. Please wait {180 - time_since_last_mine:.0f} more seconds.")
            return
        
        # new block can only be mined if previous block is valid
        get_status = last_block_status()
        if get_status == BLOCK_STATUS[0]:
            print("Previous block needs to be validated first.")
            return

        transactions = load_from_file("transactions.dat")
        transactions_to_mine = []
        indices_to_remove = []
        # Need to have 5 transactions to mine (4 transactions + mining reward)
        if len(transactions) < 4:
            print_header(username)
            print("Not enough transactions to mine.")
            return
        elif len(transactions) >= 10:
            print_header(username)
            transactions_list = get_all_transactions("transactions.dat")
            print("All Transactions: \n")
            for tx in transactions_list:
                if len(tx) > 5:
                    print(f"{str(tx[0])}. {tx[1]} to {tx[2]} with {tx[4]} transaction fee")
                else:
                    print(f"{str(tx[0])}. {tx[1]} to {tx[2]} with 0 transaction fee")
            print(f"{len(transactions)+1}. Back to main menu")
            user_choice = input(f"Enter up to 4 transaction numbers to include, separated by spaces: ").split()
            if len(user_choice) > 4:
                print_header(username)
                print(f"You can only select up to 4 transactions.")
                return  # Exit the function if the user selected too many transactions
            
            if len(user_choice) < 1:
                print_header(username)
                print("You want to select no transactions?")
                choice = input("Enter 'y' to confirm: ").lower()
                if choice != "y":    
                    return                

            for number in user_choice:
                try:
                    index = int(number) - 1
                    if index >= 0 and index < len(transactions):
                        # validate transaction
                        if transactions[index].is_valid():
                            indices_to_remove.append(index)
                            transactions_to_mine.append(transactions[index])
                        else:
                            # flag invalid transaction
                            transactions[index].validators.append((username, "invalid"))
                    else:
                        print_header(username)
                        print("Invalid input. Please enter numbers within the range.")
                        return
                except ValueError:
                    print_header(username)
                    print("Invalid input. Please enter numbers only.")
                    return
            # Filter out the user-picked transactions
            filtered_transactions = [tx for tx in transactions if tx not in transactions_to_mine]
            if len(transactions_to_mine) == 1:
                remaining_slots = 8
            elif len(transactions_to_mine) == 2:
                remaining_slots = 7
            elif len(transactions_to_mine) == 3:
                remaining_slots = 6
            elif len(transactions_to_mine) == 4:
                remaining_slots = 5
            elif len(transactions_to_mine) == 0:
                remaining_slots = 9
            sorted_transactions = sorted(filtered_transactions, key=lambda x: x.timestamp)  # Sort by timestamp
            for tx in sorted_transactions:
                if remaining_slots > 0:
                    # validate transation
                    if tx.is_valid():
                        transactions_to_mine.append(tx)
                        indices_to_remove.append(transactions.index(tx))
                        remaining_slots -= 1
                    else:
                        tx.validators.append((username, "invalid"))

        if transactions_to_mine == []:
            for tx in transactions:
                if tx.is_valid():
                    transactions_to_mine.append(tx)
                else:
                    tx.validators.append((username, "invalid"))

        # Add a reward transaction for the miner
        decrypted_private_key = fetch_decrypted_private_key(username)
        public_key = get_current_user_public_key(username)
        reward_transaction = Transaction(type = REWARD)
        # Since it's a reward, there are no inputs. 
        reward_transaction.add_output(public_key, REWARD_VALUE)
        reward_transaction.sign(decrypted_private_key)
        
        transactions_to_mine.append(reward_transaction)

        # Create a new block with the transactions and mine it
        new_block = Block(transactions_to_mine, self.chain[-1].hash, self.next_block_id())
        new_block.mine(self.difficulty, username)
        self.last_mined_timestamp = time.time()

        chain = load_from_file("blockchain.dat")
        if len(chain) > 0:
            new_block.id = len(chain)
            new_block.previous_hash = chain[-1].hash  # Update the previous_hash after mining

        # Add the new block to the blockchain
        self.add_block(new_block)
        if indices_to_remove == []:
            for tx in transactions[:-1]:  # Remove transactions in reverse order to maintain correct indices
                if tx.type == NORMAL:
                    public_key_sender = tx.input[0]
                    amount = tx.input[1]
                    public_key_receiver = tx.output[0]
                    fee = tx.fee

                    index = find_index_from_file("transactions.dat", amount, public_key_sender, public_key_receiver, fee)
                    if index is not None:
                        indices_to_remove.append(index)
                else:
                    public_key_receiver = tx.output[0]
                    index = find_index_from_file_by_public_key("transactions.dat", public_key_receiver)
                    if index is not None:
                        indices_to_remove.append(index)
        
            for index in sorted(indices_to_remove, reverse=True):
                remove_from_file("transactions.dat", index)

        else:
            for index in sorted(indices_to_remove, reverse=True):
                remove_from_file("transactions.dat", index)

    def view_blockchain(self, username=None):
        chain = load_from_file("blockchain.dat")

        if not chain:
            print_header(username)
            print("No blockchain found.")
            return
        else:
            print_header(username)
            print("The entire blockchain: \n")
            for block in chain:
                if block.previous_hash == "0":
                    print(f"Genesis Block created at: {datetime.datetime.fromtimestamp(block.timestamp).strftime('%d-%m-%Y %H:%M:%S')}")
                else:
                    block_miner = get_block_miner("blockchain.dat", chain.index(block))
                    print(f"{chain.index(block)}. Block mined by {block_miner} at: {datetime.datetime.fromtimestamp(block.timestamp).strftime('%d-%m-%Y %H:%M:%S')} [{block.status}]")

        print(f"{len(chain)}. Back to main menu\n")
        
        choice = input("Enter block to view: ")

        try:
            choice = int(choice)
        except ValueError:
            print_header(username)
            print("Please enter a correct number")
            return
        if choice > len(chain) or choice < 1:
            print_header(username)
            print("Please enter a correct number")
            return
        if choice == len(chain):
            print_header(username)
            return
        else:
            print_header(username)
            self._view_block(chain, choice, username)
            return

    def _view_block(self, chain, block_index, username=None):
        options = [
        {"option": "1", "text": "Back to blockchain", "action": lambda: self.view_blockchain()},
        {"option": "2", "text": "Back to main menu", "action": lambda: "back"}
        ]
        transactions = get_all_transactions_in_block(chain, block_index)
        block_miner = get_block_miner("blockchain.dat", block_index)
        validators = chain[block_index].validators
        transactions_to_display =  f"Block {block_index}: \n\nBlock ID: {chain[block_index].id} \nStatus: {chain[block_index].status}\nMined by {block_miner} at: {datetime.datetime.fromtimestamp(chain[block_index].timestamp).strftime('%d-%m-%Y %H:%M:%S')}\nHash: {chain[block_index].hash}\nNonce: {chain[block_index].nonce}\nPrevious_hash: {chain[block_index].previous_hash}"
        if len(validators) > 0:
            for val in validators:
                transactions_to_display += f"\n🏳️  Flagged {val[1]} by {val[0]}"
        transactions_to_display += f"\n\nAll Transactions in block: \n\n"

        for tx in transactions:
            if len(tx) == 6:
                transactions_to_display += (f"Normal Transaction: {tx[1]} coin(s) sent from {tx[3]} to {tx[2]} including a transaction fee of {tx[4]} coin(s)\n")
            else:
                transactions_to_display += (f"Reward Transaction: {tx[1]} coins credited to {tx[2]}\n")
                    

        display_menu_and_get_choice(options, username, transactions_to_display)