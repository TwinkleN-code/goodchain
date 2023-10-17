import hashlib
import os
import re
from database import Database
from keys import decrypt_private_key, read_key

def generate_random_mnemonic():
    # Make a word list
    word_list = ["lavender", "ocean", "coffee", "roses", "sandalwood", "coconut", "vanilla", "chocolate", "rain", "cinnamon"]

    # Generate random bytes
    random_bytes = os.urandom(32)

    # Calculate the checksum
    checksum_length = len(random_bytes) // 4
    checksum = hashlib.sha256(random_bytes).digest()[:checksum_length]

    # Combine the random data and checksum
    combined_data = random_bytes + checksum

    # Split the combined data into 11-bit chunks
    bits = [int.from_bytes(combined_data[i:i+11], 'big') for i in range(0, len(combined_data), 11)]

    # Create the mnemonic phrase
    mnemonic_words = []
    for bit in bits:
        word_index = bit % len(word_list)
        mnemonic_words.append(word_list[word_index])

    # Join the words
    mnemonic = " ".join(mnemonic_words)

    return mnemonic


def recover_private_key():
    db = Database()
    username = input('Enter username: ').lower()
    user_key = input("Enter recovery key: ")

    # if username exists
    if 3 <= len(username) <= 32 and re.search('^[a-zA-Z0-9]+$', username) is not None:
        retrieve_username = db.fetch('SELECT username FROM users WHERE username=?', (username, ))
        if retrieve_username and retrieve_username[0][0] == username:
            # if phrase matches
            if is_valid_phrase(user_key):
                get_hased_phrase = db.fetch('SELECT phrase FROM users WHERE username=?', (username, ))
                if get_hased_phrase and hashlib.sha256(user_key.encode()).hexdigest() == get_hased_phrase[0][0]:
                    private_key = db.fetch('SELECT privatekey FROM users WHERE username=?', (username, ))
                    db_key= read_key()
                    decrypted_private_key = decrypt_private_key(db_key, private_key[0][0])
                    print(f"\nYour private key is: \n{decrypted_private_key}")
                    return            
    print('Invalid username or key')
            


def is_valid_phrase(input_text):
    if re.match(r'^[a-zA-Z\s]+$', input_text):
        return True
    else:
        return False


