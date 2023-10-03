from auth import register_user, login_user, logout_user
from database import setup_db
from utils import print_header

current_user = None

def main_menu():
    global current_user
    print_header()
    while True:
        if current_user:
            print("┌───────────────┐")
            print("│ 1. Logout     │")
            print("│ 2. Exit       │")
            print("└───────────────┘")
        else:
            print("┌───────────────┐")
            print("│ 1. Register   │")
            print("│ 2. Login      │")
            print("│ 3. Exit       │")
            print("└───────────────┘")
        choice = input('> ')
        if not current_user:
            if choice == '1':
                register_user()
            elif choice == '2':
                current_user = login_user()
            elif choice == '3':
                break
            else:
                print_header()
                print('Invalid choice')
        else:
            if choice == '1':
                logout_user()
                current_user = None
            elif choice == '2':
                break
            else:
                print_header(current_user)
                print('Invalid choice')

setup_db()

main_menu()