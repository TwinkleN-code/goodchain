import pickle
import socket
import threading
from blockchain import Blockchain
from block_validation import block_valid
from transaction import TransactionPool
from utils import remove_from_file
from storage import load_from_file, save_to_file, blockchain_file_path_client, transactions_file_path_client
from auth import user_object

data_type = ["add block", "add transaction" , "remove transaction", "block validation", "remove block"]
miner_server_ports = [5000, 6000]
server = None
stop_server_thread = False
server_lock = threading.Lock()

def setup_server():
    global server
    for port in miner_server_ports:
        try:
            local_ip = socket.gethostbyname('localhost')
            server_address = (local_ip, port)  

            if server is not None:
                server.close()


            server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server.bind(server_address)
            server.listen()
            return server
            
        except OSError:
            continue


def start_miner_server():
    global server, stop_server_thread
    server = setup_server()
    if server is None:
        print("Failed to set up a server.")
        return

    while True:
        if stop_server_thread:
            break
        
        with server_lock:
            try:
                client_socket, address = server.accept()
            except OSError as e:
                continue
        thread = threading.Thread(target=handle_client, args=(client_socket, address))
        thread.start()

    
def handle_client(conn, addr):
    try:
        received_data = conn.recv(8888)
        if received_data:
            unpickled_data = pickle.loads(received_data)
            if unpickled_data[0] == data_type[0]:
                add_block(unpickled_data[1])
            elif unpickled_data[0] == data_type[1]:
                add_transaction(unpickled_data[1])
            elif unpickled_data[0] == data_type[2]:
                remove_transaction(unpickled_data[1])
            elif unpickled_data[0] == data_type[3]:
                block_validation(unpickled_data[1])
            elif unpickled_data[0] == data_type[4]:
                remove_block(unpickled_data[1])
    except pickle.UnpicklingError as e:
        print(f"Error data: {e}")
    except Exception as e:
        print(f"Error handling client: {e}")
    finally:
        conn.close()

def add_block(new_block):
    # add new block to local ledger
    blocks = load_from_file(blockchain_file_path_client)
    if len(blocks) > 0: 
        blocks.append(new_block)
    else:
        bc = Blockchain()
        bc.chain.append(new_block)
        blocks = bc.chain

    save_to_file(blocks, blockchain_file_path_client)

    if user_object.current_user is not None:
        block_valid(user_object.current_user) 

    
def add_transaction(transaction):
    # add transaction to local pool
    tp = TransactionPool()
    tp.add_transaction(transaction, transactions_file_path_client)

def remove_transaction(transaction):
    # remove transaction from local pool
    remove_from_file(transactions_file_path_client, transaction)

def block_validation(blockchain):
    # update ledger
    save_to_file(blockchain, blockchain_file_path_client)

def remove_block(block):
    # remove block from ledger
    remove_from_file(blockchain_file_path_client, block)

def handle_miner_termination_server():
    global stop_server_thread
    stop_server_thread = True

    if server:
        try:
            server.close()  # Close the server socket
        except Exception as e:
            print(f"Error closing server: {e}")
