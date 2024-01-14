import os
import pickle

data_folder = "data"
blockchain_file_path = os.path.join(data_folder, 'blockchain.dat')
transactions_file_path = os.path.join(data_folder, 'transactions.dat')
last_mined_timestamp_path = os.path.join(data_folder, "last_mined_timestamp.dat")

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

    if not os.path.isfile(blockchain_file_path):
        data = []
        with open(blockchain_file_path, 'wb') as file:
            pickle.dump(data, file)

    if not os.path.isfile(transactions_file_path):
        data = []
        with open(transactions_file_path, "wb") as file:
            pickle.dump(data, file)

    if not os.path.isfile(last_mined_timestamp_path):
        data = []
        with open(last_mined_timestamp_path, "wb") as file:
            pickle.dump(data, file)

setup_data_files()       