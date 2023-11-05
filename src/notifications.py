from datetime import datetime
from keys import read_key
from database import Database
from utils import display_menu_and_get_choice, print_header

class Notification:
    def __init__(self):
        self.db = Database()

    def view_notifications(self, username):
        database_key = read_key()
        id = self.get_user_id(username)
        notifications = self.db.fetch('SELECT notification FROM notifications WHERE ID=?', (id, ))
        if not notifications:
            print_header()
            print("Your notifications are empty")
            return
        for notif in reversed(notifications):
            print(notif[0])

        options = [{"option": "1", "text": "Back to main menu", "action": lambda: "back"}]
        choice_result = display_menu_and_get_choice(options)
        if choice_result == "back":
            return
        
    def add_notification(self, username, message):
        notif = self.get_current_time() + ": " + message
        id = self.get_user_id(username)
        self.db.execute('INSERT INTO notifications (ID, notification) VALUES (?, ?)', (id, notif))

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
        

        