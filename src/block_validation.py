from database import Database
from notifications import notification
from blockchain import Blockchain
from transaction import REWARD, cancel_invalid_transactions, transaction_pool
from utils import get_block_miner, remove_from_file, BLOCK_STATUS
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
            check_validators(chain, miner_username)
        else:
            #update in file
            save_to_file(chain, "blockchain.dat")
    return


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
                notification.add_notification(get_sender_username[0][0], f"successful transaction received: {tx.input[1]} coin(s) from {get_sender_username[0][0]}")
            else:
                #reward notification
                get_username = db.fetch('SELECT username FROM users WHERE publickey=?', (tx.output[0], ))
                notification.add_notification(get_username[0][0], f"reward of {tx.output[1]} coin(s) added to you balance")
        
        #change status of block 
        chain[-1].status = BLOCK_STATUS[1]

        #send notification
        notification.add_notification_to_all_users(f"block with id {chain[-1].id} verified", miner_username)
        notification.add_notification_to_all_users(f"new size of blockchain: {len(chain)}")
        notification.add_notification(miner_username, f"Your mined block with id {chain[-1].id} status changed from {BLOCK_STATUS[0]} to {BLOCK_STATUS[1]}")
        notification.add_notification(miner_username, f"Your mined block with id {chain[-1].id} is verified")

    elif invalid_flags >= 3:
        chain[-1].status = BLOCK_STATUS[2]
        list_transactions = chain[-1].transactions
        # put transactions back in pool
        for tx in list_transactions[:-1]: #skips the reward transaction of miner
            transaction_pool.add_transaction(tx)

        # remove block from blockchain
        remove_from_file("blockchain.dat", len(chain)-1)

        #notify user's rejected block
        notification.add_notification(miner_username, f"Your mined block with id {chain[-1].id} is rejected")
        return

    #update in file
    save_to_file(chain, "blockchain.dat")
    return

def automatic_tasks(username):
    # check if a new block is added but not yet validated bij enough nodes
    block_valid(username)

    # check if user has invalid transactions and cancel it
    cancel_invalid_transactions(username)



def validation_chain():
    block_chain = Blockchain()
    block_chain.chain = load_from_file("blockchain.dat")
    if block_chain.blockchain_is_valid():
        print("Blockchain has valid blocks")
    else:
        print("Blockchain has invalid block(s)")
