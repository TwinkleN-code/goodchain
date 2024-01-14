from datetime import datetime
from threading import Lock
from keys import decrypt, encrypt, read_key
from database import Database
from utils import display_menu_and_get_choice, print_header
from wallet_client import data_type_wallet, send_data_to_wallet_servers

class Notification:
    def __init__(self):
        self.db = Database()
        self.database_key = read_key()
        self.lock = Lock()

    def view_notifications(self, username):
        print_header(username)
        id = self.get_user_id(username)
        notifications = self.db.fetch('SELECT notification FROM notifications WHERE ID=?', (id, ))
        decrypted_notif = "\nYour notifications:\n\n"
        if not notifications:
            print_header(username)
            print("Your notifications are empty")
            return
        for notif in reversed(notifications):
            decrypted_notif += decrypt(notif[0], self.database_key) + "\n"

        options = [{"option": "1", "text": "Back to main menu", "action": lambda: "back"}]
        choice_result = display_menu_and_get_choice(options, username, decrypted_notif)
        if choice_result == "back":
            print_header(username)
            return
        
    def add_notification(self, username, message):
        with self.lock:   
            notif = self.get_current_time() + ": " + message
            #encrypt info
            encrypted_notif = encrypt(notif, self.database_key)
            id = self.get_user_id(username)
            self.db.execute('INSERT INTO notifications (ID, notification) VALUES (?, ?)', (id, encrypted_notif))


    def add_notification_to_all_users(self, message, exclude_user=None):            
        list_user = self.get_all_users()
        for user in list_user:
            if exclude_user != user:
                self.add_notification(user, message)
        
    def get_current_time(self):
        return (datetime.now()).strftime("%d-%m-%Y %H:%M")
    
    def get_user_id(self, username):
        result = self.db.fetch("SELECT ID FROM users WHERE username=?", (username, ))
        if result:
            return result[0][0]
        return None
    
    def get_all_users(self):
        results = self.db.fetch("SELECT username FROM users")
        return [result[0] for result in results] if results else []
        
notification = Notification()
        

        