import os

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def print_header(username=None):
    clear_screen()
    header =("##################")
    title = ("#   GOODCHAIN    #")

    if username:
        print("Logged in as: " + username + "\n")

    print(header)
    print(title)
    print(header)
    print("")