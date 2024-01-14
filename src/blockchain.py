import time
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from notifications import notification
from transaction import REWARD_VALUE, REWARD, Transaction, transaction_pool
from keys import fetch_decrypted_private_key
from storage import *
from utils import *
import os
import datetime
from miner_client import send_data_to_miner_servers, data_type_miner
from wallet_client import send_data_to_wallet_servers, data_type_wallet
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
        self.difficulty = DIFFICULTY

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
        return difficulty

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
        calculate_hash = self.compute_hash()
        if self.hash != calculate_hash:
            return False

        #check if block's hash meets the difficulty requirement
        if not self.hash[:self.difficulty] == '0' * self.difficulty:
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
        genesis_block.status = BLOCK_STATUS[3]
        return genesis_block
    
    def next_block_id(self):
        return len(self.chain)

    def add_block(self, block):
        # A function to add the block to the blockchain after it's mined.
        self.chain.append(block)
        self._save_block_to_file(block)

    def _save_block_to_file(self, block):
        blocks = load_from_file(blockchain_file_path)
        if len(blocks) > 0: 
            blocks.append(block)
        else:
            blocks = self.chain
        save_to_file(blocks, blockchain_file_path)
        save_to_file(self.last_mined_timestamp, last_mined_timestamp_path)

    def _load_last_mined_timestamp(self):
        # Check if the file exists
        if os.path.exists(last_mined_timestamp_path):
            time_stamp = load_from_file(last_mined_timestamp_path)
            if time_stamp:
                # Load the last mined timestamp from the file
                return time_stamp[0]
            else:
                # If the file does not exist, return a default value of 0
                return 0
        
    def blockchain_is_valid(self, current_user):
        invalid_blocks = []
        valid_pending_blocks = []
        # Check for genesis block
        if not self.chain:
            return True
        
        previous_hash = "0"

        # Start with the last block and validate chain integrity
        for i, current_block in enumerate(self.chain):
            # Skip genesis block but check its previous hash
            if i == 0:
                if current_block.previous_hash != "0":
                    print("Genesis block's previous hash should be '0'.")
                    return False
                previous_hash = current_block.hash
                continue

            skip_block = False
            # check if block is already validated by user
            if current_block.validators:
                for user, type in current_block.validators:
                    if current_user == user:
                        skip_block = True
                        break
            
            if skip_block:
                continue

            # check if block is created by miner
            if i != 0:
                miner_username = get_username_miner(blockchain_file_path, i)
                if miner_username == current_user:
                    continue


            current_hash = current_block.compute_hash()    

            # 1. Check the previous_hash of the current block
            if current_block.previous_hash != previous_hash:
                print(f"Previous block hash in block {i} doesn't match with stored previous hash value.")
                current_block.validators.append((current_user, "invalid"))  
                if current_block.id not in invalid_blocks:  
                    invalid_blocks.append(current_block.id)

            # 2. Check the hash of the current block
            if current_block.hash != current_hash:
                print(f"Hash of the block {i} is not valid.")
                current_block.validators.append((current_user, "invalid"))  
                if current_block.id not in invalid_blocks:  
                    invalid_blocks.append(current_block.id)


            # 3. Check if block's hash meets the difficulty requirement
            if not current_hash[:self.difficulty] == '0' * self.difficulty:
                print(f"Hash value in block {i} doesn't meet the difficulty requirements.")
                current_block.validators.append((current_user, "invalid"))
                if current_block.id not in invalid_blocks:  
                    invalid_blocks.append(current_block.id)

            # 4. Validate all transactions in the block
            for transaction in current_block.transactions:
                if not transaction.is_valid():
                    print(f"Transaction {transaction} in block {i} is not valid.")
                    current_block.validators.append((current_user, "invalid"))
                    if current_block.id not in invalid_blocks:  
                        invalid_blocks.append(current_block.id)

            # if block status is on pending add a valid flag
            if current_block.status == BLOCK_STATUS[0] and current_block.id not in invalid_blocks:
                current_block.validators.append(current_user, "valid")
                valid_pending_blocks.append(current_block.id)
                
            previous_hash = current_hash

        #update ledger
        if invalid_blocks or valid_pending_blocks:
            save_to_file(self.chain, blockchain_file_path)
            # update invalid blocks to servers
            send_data_to_miner_servers((data_type_miner[3], self.chain))

            #check if 3 flags
            check_validators(self.chain, current_user)
            
        return invalid_blocks

    def mine_transactions(self, username):
        print_header(username)
        # add 3 minutes time interval
        current_timestamp = time.time()
        if self.last_mined_timestamp == None:
            self.last_mined_timestamp = 0
        time_since_last_mine = current_timestamp - self.last_mined_timestamp
        invalid_tx = []
        if time_since_last_mine < 180:  # 180 seconds = 3 minutes
            print(f"Too soon to mine again. Please wait {180 - time_since_last_mine:.0f} more seconds.")
            return
        
        # new block can only be mined if every block is valid
        load_chain = load_from_file(blockchain_file_path)
        if load_chain:
            for block in reversed(load_chain):
                if block.status != BLOCK_STATUS[1] and block.id != 0 and block.previous_hash != "0":
                    print(f"Mining is not possible until the validation of block {block.id} is completed.")
                    return

        transactions = load_from_file(transactions_file_path)
        transactions_to_mine = []
        indices_to_remove = []
        # Need to have 5 transactions to mine (4 transactions + mining reward)
        if len(transactions) < 4:
            print("Not enough transactions to mine.")
            return
        elif len(transactions) >= 10:
            transactions_list = get_all_transactions(transactions_file_path)
            print("All Transactions: \n")
            for tx in transactions_list:
                if len(tx) > 6:
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
                        check_if_already_validated = any(name == username for name, _ in transactions[index].validators)
                        if not check_if_already_validated:
                            # validate transaction
                            if transactions[index].is_valid():
                                indices_to_remove.append(index)
                                transactions_to_mine.append(transactions[index])
                            else:
                                # flag invalid transaction
                                transactions[index].validators.append((username, "invalid"))
                                # remove and update the transaction
                                indices_to_remove.append(index)
                                invalid_tx.append(transactions[index])
                    else:
                        print("Invalid input. Please enter numbers within the range.")
                        return
                except ValueError:
                    print("Invalid input. Please enter numbers only.")
                    return
            # Filter out the user-picked transactions
            filtered_transactions = [tx for tx in transactions if tx not in transactions_to_mine]
            for i in range(5):
                if len(transactions_to_mine) == i:
                    remaining_slots = 9 - i
                    break

            sorted_transactions = sorted(filtered_transactions, key=lambda x: x.timestamp)  # Sort by timestamp
            for tx in sorted_transactions:
                if remaining_slots > 0:
                    check_if_already_validated = any(name == username for name, _ in tx.validators)
                    if not check_if_already_validated:
                        # validate transation
                        if tx.is_valid():
                            transactions_to_mine.append(tx)
                            indices_to_remove.append(transactions.index(tx))
                            remaining_slots -= 1
                        else:
                            tx.validators.append((username, "invalid"))
                            indices_to_remove.append(transactions.index(tx)) 
                            invalid_tx.append(transactions[index])
                else:
                    break

        if transactions_to_mine == []:
            for tx in transactions:
                check_if_already_validated = any(name == username for name, _ in tx.validators)
                if not check_if_already_validated:
                    if tx.is_valid():
                        transactions_to_mine.append(tx)
                        indices_to_remove.append(transactions.index(tx))
                    else:
                        tx.validators.append((username, "invalid"))
                        indices_to_remove.append(transactions.index(tx))
                        invalid_tx.append(tx)

        # if all transactions from pool are invalid, there is nothing to mine
        if transactions_to_mine == [] and indices_to_remove == []:
            print("There are no valid transactions to mine")
            return
        # if there are invalid transactions found and there is no valid transaction to mine
        elif transactions_to_mine == [] and indices_to_remove != []: 
            # updated invalid transactions
            print("There are no valid transactions to mine")
            return
        elif len(transactions_to_mine) < 4:
            print("Not enough transactions to mine.")
            return
        else:
            # Add a reward transaction for the miner
            decrypted_private_key = fetch_decrypted_private_key(username)
            public_key = get_current_user_public_key(username)
            reward_transaction = Transaction(type = REWARD)
            # Since it's a reward, there are no inputs. 
            reward_transaction.add_output(public_key, REWARD_VALUE)
            reward_transaction.sign(decrypted_private_key)
            
            transactions_to_mine.append(reward_transaction)
            
            # Create a new block with the transactions and mine it
            if len(load_chain) > 0:
                new_block = Block(transactions_to_mine, load_chain[-1].hash, len(load_chain))
            else:  
                new_block = Block(transactions_to_mine, self.chain[-1].hash, self.next_block_id())
            result_diff = new_block.mine(self.difficulty, username)
            new_block.difficulty = result_diff
            self.last_mined_timestamp = time.time()

            # Add the new block to the blockchain
            self.add_block(new_block) # adding to the main ledger

            # send new block from client to servers
            send_data_to_miner_servers((data_type_miner[0], new_block))

            # add notification to user
            notification.add_notification_to_all_users(f"new added block with id {new_block.id} waiting for verification", username)
            notification.add_notification(username, f"pending mining reward of {REWARD_VALUE} coin(s) added to block waiting for verification")

            send_data_to_wallet_servers((data_type_wallet[4], f"new added block with id {new_block.id} waiting for verification", username))

        # removing transactions from pool
        for index in sorted(indices_to_remove, reverse=True):
            remove_from_file(transactions_file_path, index) # remove from main pool
            # send transaction to servers 
            send_data_to_miner_servers((data_type_miner[2], index))
        
        # update invalid transactions
        if invalid_tx:
            for tx in invalid_tx:
                transaction_pool.add_transaction(tx, transactions_file_path) # add to main pool
                # send transaction to servers
                send_data_to_miner_servers((data_type_miner[1], tx))

    def view_blockchain(self, username=None):
        print_header(username)
        chain = load_from_file(blockchain_file_path) 
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
                    block_miner = get_username_miner(blockchain_file_path, chain.index(block))
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
        {"option": "1", "text": "Back to blockchain", "action": lambda: self.view_blockchain(username)},
        {"option": "2", "text": "Back to main menu", "action": lambda: "back"}
        ]
        transactions = get_all_transactions_in_block(chain, block_index)
        block_miner = get_username_miner(blockchain_file_path, block_index)
        validators = chain[block_index].validators
        transactions_to_display =  f"Block {block_index}: \n\nBlock ID: {chain[block_index].id} \nStatus: {chain[block_index].status}\nMined by {block_miner} at: {datetime.datetime.fromtimestamp(chain[block_index].timestamp).strftime('%d-%m-%Y %H:%M:%S')}\nHash: {chain[block_index].hash}\nNonce: {chain[block_index].nonce}\nDifficulty: {chain[block_index].difficulty}\nPrevious_hash: {chain[block_index].previous_hash}"
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


def check_validators(chain, miner_username):
    invalid_flags = 0
    valid_flags = 0
    db = Database()

    for validator in chain[-1].validators:
        if validator[1] == "valid":
            valid_flags += 1
        elif validator[1] == "invalid":
            invalid_flags += 1

    if valid_flags >= 3:
        for tx in chain[-1].transactions:
            if tx.input != None:            
                #notify succesful transactions 
                get_sender_username = db.fetch('SELECT username FROM users WHERE publickey=?', (tx.input[0], ))
                receiver_username = db.fetch('SELECT username FROM users WHERE publickey=?', (tx.output[0], ))
                notification.add_notification(get_sender_username[0][0], f"successful transaction: {tx.input[1]} coin(s) to {receiver_username[0][0]}")
                notification.add_notification(receiver_username[0][0], f"successful transaction received: {tx.input[1]} coin(s) from {get_sender_username[0][0]}")
                send_data_to_wallet_servers((data_type_wallet[3], get_sender_username[0][0], f"successful transaction: {tx.input[1]} coin(s) to {receiver_username[0][0]}"))
                send_data_to_wallet_servers((data_type_wallet[3], receiver_username[0][0], f"successful transaction received: {tx.input[1]} coin(s) from {get_sender_username[0][0]}"))
            else:
                #reward notification
                get_username = db.fetch('SELECT username FROM users WHERE publickey=?', (tx.output[0], ))
                notification.add_notification(get_username[0][0], f"reward of {tx.output[1]} coin(s) added to you balance")
                send_data_to_wallet_servers((data_type_wallet[3], get_username[0][0], f"reward of {tx.output[1]} coin(s) added to you balance"))
        
        #change status of block 
        chain[-1].status = BLOCK_STATUS[1]

        #send notification
        notification.add_notification_to_all_users(f"block with id {chain[-1].id} verified and added to the blockchain", miner_username)
        notification.add_notification_to_all_users(f"new size of blockchain: {len(chain)}")
        notification.add_notification(miner_username, f"Your mined block with id {chain[-1].id} status changed from {BLOCK_STATUS[0]} to {BLOCK_STATUS[1]}")
        notification.add_notification(miner_username, f"Your mined block with id {chain[-1].id} is verified and added to the blockchain")

        #send notification to servers
        send_data_to_wallet_servers((data_type_wallet[4], f"block with id {chain[-1].id} verified and added to the blockchain", miner_username))
        send_data_to_wallet_servers((data_type_wallet[4], f"new size of blockchain: {len(chain)}"))
        send_data_to_wallet_servers((data_type_wallet[3], miner_username, f"Your mined block with id {chain[-1].id} status changed from {BLOCK_STATUS[0]} to {BLOCK_STATUS[1]}"))
        send_data_to_wallet_servers((data_type_wallet[3], miner_username, f"Your mined block with id {chain[-1].id} is verified and added to the blockchain"))

    elif invalid_flags >= 3:
        chain[-1].status = BLOCK_STATUS[2]
        list_transactions = chain[-1].transactions
        # put transactions back in pool
        for tx in list_transactions[:-1]: #skips the reward transaction of miner
            transaction_pool.add_transaction(tx, transactions_file_path)
            # send transaction to servers
            send_data_to_miner_servers((data_type_miner[1], tx))

        # remove block from blockchain
        remove_from_file(blockchain_file_path, len(chain)-1)
        # send block to servers
        send_data_to_miner_servers((data_type_miner[4], len(chain)-1))

        if chain[-1].id == 1:
            remove_from_file(blockchain_file_path, 0)
            send_data_to_miner_servers((data_type_miner[4], 0))

        #notify user's rejected block
        notification.add_notification(miner_username, f"Your mined block with id {chain[-1].id} is rejected")
        send_data_to_wallet_servers((data_type_wallet[3], miner_username, f"Your mined block with id {chain[-1].id} is rejected"))
        return

    #update ledger
    save_to_file(chain, blockchain_file_path)
    send_data_to_miner_servers((data_type_miner[3], chain))
    return