import os
import pickle
import shutil

data_folder = "data"
blockchain_file_path = os.path.join(data_folder, 'blockchain.dat')
transactions_file_path = os.path.join(data_folder, 'transactions.dat')
#last_mined_timestamp_path = os.path.join(data_folder, "last_mined_timestamp.dat")

node_data = "node_data"

def save_to_file(data, filename):
    with open(filename, "wb") as file:
        pickle.dump(data, file)

def load_from_file(filename):
    try:
        with open(filename, "rb") as file:
            data = pickle.load(file)
            if not isinstance(data, list):
                return [data]
            return data
    except (FileNotFoundError, EOFError, pickle.UnpicklingError, ValueError) as e:
        print(f"Error loading from {filename}: {e}")
        return []
    
def setup_data_files():
    if not os.path.exists(data_folder):
        os.makedirs(data_folder)

    if not os.path.exists(node_data):
        os.makedirs(node_data)

    if not os.path.isfile(blockchain_file_path):
        data = []
        with open(blockchain_file_path, 'wb') as file:
            pickle.dump(data, file)

    if not os.path.isfile(transactions_file_path):
        data = []
        with open(transactions_file_path, "wb") as file:
            pickle.dump(data, file)

    # if not os.path.isfile(last_mined_timestamp_path):
    #     data = []
    #     with open(last_mined_timestamp_path, "wb") as file:
    #         pickle.dump(data, file)

def setup_local_data(foldername):

    count = 1 
    # make local copies for the node
    client_data_folder = os.path.join(node_data, foldername + "_" + str(count))
    while os.path.exists(client_data_folder):
        count += 1
        client_data_folder = os.path.join(node_data, foldername + "_" + str(count))
    os.makedirs(client_data_folder)

    blockchain_file_path_client = os.path.join(client_data_folder, 'blockchain.dat')
    transactions_file_path_client = os.path.join(client_data_folder, 'transactions.dat')
    last_mined_timestamp_path_client = os.path.join(client_data_folder, "last_mined_timestamp.dat")
    db_path = os.path.join(data_folder, "users.db")
    db_path_client = os.path.join(client_data_folder, "users.db")

    try:
        shutil.copy(blockchain_file_path, client_data_folder)
        shutil.copy(transactions_file_path, client_data_folder)
        shutil.copy(db_path, client_data_folder)
    except FileNotFoundError:
        print("File not found")
    except PermissionError:
        print("Permission of file denied")

    if not os.path.isfile(last_mined_timestamp_path_client):
        data = []
        with open(last_mined_timestamp_path_client, "wb") as file:
            pickle.dump(data, file)

    return client_data_folder, blockchain_file_path_client, transactions_file_path_client, last_mined_timestamp_path_client, db_path_client

client_data_folder, blockchain_file_path_client, transactions_file_path_client, last_mined_timestamp_path_client, db_path_client = setup_local_data("local_data")
