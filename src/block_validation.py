from blockchain import Blockchain, check_validators
from transaction import cancel_invalid_transactions
from utils import display_menu_and_get_choice, get_block_miner, print_header, BLOCK_STATUS
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

def automatic_tasks(username):
    # check if a new block is added but not yet validated bij enough nodes
    block_valid(username)

    # check if user has invalid transactions and cancel it
    cancel_invalid_transactions(username)



def validation_chain(current_user):
    print_header(current_user)
    block_chain = Blockchain()
    block_chain.chain = load_from_file("blockchain.dat")
    # if file is empty return
    if not block_chain.chain:
        print("Validation is not possible as the blockchain is currently empty.")
        return
    result = block_chain.blockchain_is_valid(current_user)
    if len(result) == 0:
        print("Blockchain has valid blocks")
    else:
        result_str = ', '.join(map(str, result))
        print(f"Blocks with id: {result_str} are invalid")

    options = [{"option": "1", "text": "Back to main menu", "action": lambda: "back"}]
    choice_result = display_menu_and_get_choice(options)
    if choice_result == "back":
        return
