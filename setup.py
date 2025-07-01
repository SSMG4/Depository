import os
import sys
import subprocess

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def print_banner():
    banner = r"""
  ____       _                         _ _                   
 / ___|  ___| |_ _   _ _ __   ___  ___(_) |_ ___  _ __ _   _ 
 \___ \ / _ \ __| | | | '_ \ / _ \/ __| | __/ _ \| '__| | | |
  ___) |  __/ |_| |_| | |_) | (_) \__ \ | || (_) | |  | |_| |
 |____/ \___|\__|\__,_| .__/ \___/|___/_|\__\___/|_|   \__, |
                      |_|                              |___/  

   Universal Setup Installer for MDepository & Depository
    """
    print(banner)

def install_packages():
    packages = ['requests', 'gitpython', 'tqdm']
    print("Installing required Python packages...\n")
    try:
        # Run pip install for all packages at once
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', *packages])
        print("\nAll packages installed successfully!")
    except subprocess.CalledProcessError:
        print("\nOops, something went wrong while installing packages.")
        print("Try running this script with administrator/root privileges.")
        sys.exit(1)

def main_menu():
    clear_screen()
    print_banner()
    print("What do you want to do?")
    print("1. Install required Python packages")
    print("2. Exit")
    choice = input("\nEnter your choice (1 or 2): ").strip()
    while choice not in ('1', '2'):
        print("Invalid choice. Please enter 1 or 2.")
        choice = input("Enter your choice: ").strip()
    return choice

def main():
    while True:
        choice = main_menu()
        if choice == '1':
            install_packages()
            input("\nPress Enter to exit...")
            break
        else:
            print("Goodbye!")
            break

if __name__ == "__main__":
    main()
