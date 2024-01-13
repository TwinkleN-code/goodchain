import pickle
import socket
import threading


data_type = ["new user", "update password", "update username"]
wallet_server_ports = [8000, 9000]
server = None
stop_server_thread = False

def setup_server():
    global server
    for port in wallet_server_ports:
        try:
            local_ip = socket.gethostbyname('localhost')
            server_address = (local_ip, port)           
            server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server.bind(server_address)
            server.listen()
            return server
            
        except OSError:
            continue

def start_wallet_server():
    global server, stop_server_thread
    server = setup_server()

    while True:
        if stop_server_thread:
            break
        
        client_socket, address = server.accept()
        thread = threading.Thread(target=handle_client, args=(client_socket, address))
        thread.start()


def handle_client(conn, addr):
    try:
        received_data = conn.recv(8888)
        if received_data:
            unpickled_data = pickle.loads(received_data)
            if unpickled_data[0] == data_type[0]:
                new_user(unpickled_data[1])
            elif unpickled_data[0] == data_type[1]:
                update_password(unpickled_data[1])
            elif unpickled_data[0] == data_type[2]:
                update_username(unpickled_data[1])
    except pickle.UnpicklingError as e:
        print(f"Error data: {e}")
    except Exception as e:
        print(f"Error handling client: {e}")
    finally:
        conn.close()

def new_user(user):
    # add new user to local database
    pass

def update_password(user):
    # update password in local database
    pass

def update_username(user):
    # update username in local database
    pass