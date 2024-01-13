import pickle
import socket
import threading
import sqlite3
from transaction import TransactionPool
from database import Database
from keys import save_key

db = Database()

data_type_wallet = ["new user", "update password", "update username"]
wallet_server_ports = [8000, 9000]
server = None
stop_server_thread = False
server_lock = threading.Lock()

def setup_server():
    global server
    for port in wallet_server_ports:
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

def start_wallet_server():
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
            if unpickled_data[0] == data_type_wallet[0]:
                new_user(unpickled_data[1:])
            elif unpickled_data[0] == data_type_wallet[1]:
                update_password(unpickled_data[1:])
            elif unpickled_data[0] == data_type_wallet[2]:
                update_username(unpickled_data[1:])
    except pickle.UnpicklingError as e:
        print(f"Error data: {e}")
    except Exception as e:
        print(f"Error handling client: {e}")
    finally:
        conn.close()

def new_user(username, password, public_key, private_key, phrase):
    # add new user to local database
    try:
        db.execute('INSERT INTO users (username, password, privatekey, publickey, phrase) VALUES (?, ?, ?, ?, ?)', (username, password, private_key, public_key, phrase))
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return
    # update key file
    save_key(private_key)

def update_password(user, new_password):
    # update password in local database
    try:
        db.execute('UPDATE users SET password=? WHERE username=?', (new_password, user))
    except sqlite3.Error as e:
        print(f"Database error: {e}")

def update_username(user, new_username):
    # update username in local database
    try:
        db.execute('UPDATE users SET username=? WHERE username=?', (new_username, user))
    except sqlite3.IntegrityError:
        print('Username is already taken')

def handle_wallet_termination_server():
    global stop_server_thread
    stop_server_thread = True

    if server:
        try:
            server.close()  # Close the server socket
        except Exception as e:
            print(f"Error closing server: {e}")