import pickle

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