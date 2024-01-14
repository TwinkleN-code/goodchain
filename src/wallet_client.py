import pickle
import socket
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)

data_type_miner = ["add block", "add transaction", "remove transaction", "block validation", "remove block"]
data_type_wallet = ["new user", "update password", "update username", "add notification", "add notification to all users"]
server_ip = '192.168.178.101'
wallet_server_port = 8080
miner_server_port = 9090


def send_data_to_wallet_servers(*data):
    server_address = (server_ip, wallet_server_port)

    try:
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect(server_address)
        logging.info(f"Connected to server at {server_address}")

        # Serialize the data
        serialized_data = pickle.dumps(data)
        client.sendall(serialized_data)
        logging.info(f"Sent data to the server: {data}")

        client.close()
    except ConnectionRefusedError as e:
        logging.error(f"Failed to connect to server: {e}")
    except Exception as e:
        logging.error(f"Error in sending data: {e}")

def send_data_to_miner_servers(data):
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