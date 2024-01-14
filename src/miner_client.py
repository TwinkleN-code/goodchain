import pickle
import socket

data_type_miner = ["add block", "add transaction", "remove transaction", "block validation", "remove block", "update transaction"]
#miner_server_port = 9000 #2
miner_server_port = 9090
         
def send_data_to_miner_servers(data):
    server_ip = '192.168.178.101'   
    server_address = (server_ip, miner_server_port)

    try:
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect(server_address)
        
        # Serialize the data
        serialized_data = pickle.dumps(data)
        client.sendall(serialized_data)
        
        client.close()
    except ConnectionRefusedError:
        exit()
