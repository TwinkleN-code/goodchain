import pickle
import socket
import threading

data_type = ["add block", "add transaction" , "remove transaction", "block validation"]
server_ports = [5000, 6000]

def setup_server():
    for port in server_ports:
        try:
            local_ip = socket.gethostbyname('localhost')
            server_address = (local_ip, port)
            
            server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server.bind(server_address)
            server.listen()
            
            #print(f"Server started on address: {server_address}")
            return server
            
        except OSError:
            continue


def start_miner_server():
    server = setup_server()
    while True:
        client_socket, address = server.accept()
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
    except pickle.UnpicklingError as e:
        print(f"Error data: {e}")
    except Exception as e:
        print(f"Error handling client: {e}")
    finally:
        conn.close()

def add_block(block):
    # add block to ledger
    print("received block")
    pass

def add_transaction(transaction):
    # add transaction 
    pass

def remove_transaction(transaction):
    # remove transaction from pool
    pass

def block_validation(block):
    # update blockchain
    pass
           
# def send_msg(conn, msg):
#     conn.send(msg.encode(FORMAT))
#     print(f'Message sent: {msg}')
    


