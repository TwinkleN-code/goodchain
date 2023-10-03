import os

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def print_header(username=None):
    clear_screen()

    header_username = ("##################")
    header =("##################")
    title = ("#   GOODCHAIN    #")

    if username:
        terminal_width = os.get_terminal_size().columns
        logged_in_str = "Logged in as " + username
        padding_required = terminal_width - len(header_username) - len(logged_in_str)
        header_username += " " * padding_required + logged_in_str
        print(header_username)
    else:
        print(header)

    print(title)
    print(header)
    print("")