import pickle
import socket

data_type_miner = ["add block", "add transaction", "remove transaction", "block validation", "remove block", "update transaction"]
data_type_wallet = ["new user", "update password", "update username"]
wallet_server_ports = [8000, 9000]
miner_server_ports = [5000, 6000]

def send_data_to_wallet_servers(*data):
    local_ip = socket.gethostbyname('localhost')
    
    for port in wallet_server_ports:
        server_address = (local_ip, port)

        try:
            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client.connect(server_address)
            
            # Serialize the data
            serialized_data = pickle.dumps(data)
            client.sendall(serialized_data)
            
            client.close()
        except ConnectionRefusedError:
            continue

def send_data_to_miner_servers(data):
    local_ip = socket.gethostbyname('localhost')
    
    for port in miner_server_ports:
        server_address = (local_ip, port)

        try:
            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client.connect(server_address)
            
            # Serialize the data
            serialized_data = pickle.dumps(data)
            client.sendall(serialized_data)
            
            client.close()
        except ConnectionRefusedError:
            continue