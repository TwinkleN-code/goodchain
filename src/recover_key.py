# import re
# from database import Database
# from keys import decrypt_private_key, read_key


# def generate_recovery_phrase():
#     mnemo = mnemonic.Mnemonic("english")
#     return mnemo.generate(strength=128)  # 12 words for 128 bits 


# def recover_private_key():
#     db = Database()

#     while True:
#         username = input('Enter username: ').lower()
#         if 3 <= len(username) <= 32 and re.search('^[a-zA-Z0-9]+$', username) is not None:
#                 retrieve_username = db.fetch('SELECT username FROM users WHERE username=?', (username, ))
#                 if retrieve_username[0][0] == username:
#                     break
#                 else:
#                     print("Username does not exists")
#         else:
#             print('Invalid input. try again')

#     get_hased_phrase = db.fetch('SELECT phrase FROM users WHERE username=?', (username, ))
    
#     while True:
#         user_key = input("Enter recovery key: ")
#         if is_valid_phrase(user_key) is True:
#             if bcrypt.checkpw(user_key.encode('utf-8'), get_hased_phrase[0][0]):
#                 private_key = db.fetch('SELECT privatekey FROM users WHERE username=?', (username, ))
#                 db_key= read_key()
#                 decrypted_private_key = decrypt_private_key(db_key, private_key[0][0])
#                 print(f"\nYour private key is: \n{decrypted_private_key}")
#                 return
#             else:
#                 print("Incorrect phrase")
#                 return
#         else:
#             print('Invalid input. try again')

# def is_valid_phrase(input_text):
#     if re.match(r'^[a-zA-Z\s]+$', input_text):
#         return True
#     else:
#         return False


