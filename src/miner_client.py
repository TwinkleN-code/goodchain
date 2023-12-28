import pickle
import socket

data_type = ["add block", "add transaction" , "remove transaction", "block validation"]
server_ports = [5000, 6000]
         
def send_data_to_all_servers(data):
    local_ip = socket.gethostbyname('localhost')
    
    for port in server_ports:
        server_address = (local_ip, port)

        try:
            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client.connect(server_address)
            #print("Client connected to server with address:", server_address)
            
            # Serialize the data
            serialized_data = pickle.dumps(data)
            client.sendall(serialized_data)
            
            client.close()
        except ConnectionRefusedError:
            continue
    