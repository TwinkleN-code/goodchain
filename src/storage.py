import os
import pickle

subfolder = "data"
blockchain_file_path = os.path.join(subfolder, 'blockchain.dat')
transactions_file_path = os.path.join(subfolder, 'transactions.dat')
last_mined_timestamp_path = os.path.join(subfolder, "last_mined_timestamp.dat")

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
    if not os.path.exists(subfolder):
        os.makedirs(subfolder)

    

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