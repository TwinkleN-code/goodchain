from keys import fetch_decrypted_private_key
from database import Database
from transaction import REWARD, Transaction, transaction_pool
from utils import get_block_miner, get_current_user_public_key, remove_from_file, BLOCK_STATUS
from storage import load_from_file, save_to_file


def block_valid(current_user):
    # check if there is a pending block
    chain = load_from_file("blockchain.dat")

    if len(chain) <= 1:
        return
    
    previous_block = chain[-2] if len(chain) > 2 else chain[0]
    miner_username = get_block_miner("blockchain.dat", -1)
    # if there is a pending block
    if chain[-1].status == BLOCK_STATUS[0] and miner_username != current_user:
        # check if already validated by current user
        if chain[-1].validators:
            for user, type in chain[-1].validators:
                if user == current_user:
                    return
        # check if block is valid
        validation = chain[-1].is_valid(previous_block, current_user)
        # flag it
        if validation:
            chain[-1].validators.append((current_user, "valid"))                               
        else:
            chain[-1].validators.append((current_user, "invalid"))
        
        # check if there are enough validators
        if len(chain[-1].validators) >= 3:
            check_validators(chain, current_user, miner_username)
        else:
            #update in file
            save_to_file(chain, "blockchain.dat")
    return


def check_validators(chain, current_user, miner_username):
    invalid_flags = 0
    valid_flags = 0

    for validator in chain[-1].validators:
        if validator[1] == "valid":
            valid_flags += 1
        elif validator[1] == "invalid":
            invalid_flags += 1

    if valid_flags >= 3:
        for tx in chain[-1].transactions:
            #send transaction fee to miner if transaction type is not reward
            if tx.input != None:
                db = Database()
                get_sender_username = db.fetch('SELECT username FROM users WHERE publickey=?', (tx.input[0], ))
                sender_private_key = fetch_decrypted_private_key(get_sender_username[0][0])
                public_key_receiver = get_current_user_public_key(miner_username)
                transaction = Transaction(0, 0)
                transaction.add_input(tx.input[0], tx.fee)
                transaction.add_output(public_key_receiver,tx.fee)
                transaction.sign(sender_private_key)
                transaction_pool.add_transaction(transaction)
        
        #change status of block 
        chain[-1].status = BLOCK_STATUS[1]

    elif invalid_flags >= 3:
        chain[-1].status = BLOCK_STATUS[2]
        # put transactions back in pool
        for tx in chain[-1].transactions:
            transaction_pool.add_transaction(tx)

        # remove block from blockchain
        remove_from_file("blockchain.dat", len(chain)-1)
        return

    #update in file
    save_to_file(chain, "blockchain.dat")
    return

def automatic_tasks(username):
    # check if a new block is added but not yet validated bij enough nodes
    block_valid(username)

def last_block_status():
    chain = load_from_file("blockchain.dat")
    if chain:
        return chain[-1].status
    return None