"""
setup.py  —  Dependency installer for Depository & MDepository.
Run this once before using either tool.
"""

import os
import sys
import subprocess


REQUIRED_PACKAGES = ["requests", "gitpython", "tqdm"]

BANNER = r"""
  ____       _                         _ _                   
 / ___|  ___| |_ _   _ _ __   ___  ___(_) |_ ___  _ __ _   _ 
 \___ \ / _ \ __| | | | '_ \ / _ \/ __| | __/ _ \| '__| | | |
  ___) |  __/ |_| |_| | |_) | (_) \__ \ | || (_) | |  | |_| |
 |____/ \___|\__|\__,_| .__/ \___/|___/_|\__\___/|_|   \__, |
                      |_|                              |___/  

         Depository Setup  --  Dependency Installer
"""


def clear_screen():
    os.system("cls" if os.name == "nt" else "clear")


def check_python_version():
    ver = sys.version_info
    ver_str = f"Python {ver.major}.{ver.minor}.{ver.micro}"
    print(f"  Detected: {ver_str}")
    if ver < (3, 10):
        print(f"\n  WARNING: {ver_str} is not supported.")
        print("  Depository requires Python 3.10 or newer.")
        print("  Please upgrade at https://www.python.org/downloads/")
        input("\n  Press Enter to exit...")
        sys.exit(1)


def install_packages():
    print(f"\n  Installing: {', '.join(REQUIRED_PACKAGES)}\n")
    try:
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "--upgrade", *REQUIRED_PACKAGES]
        )
        print("\n  All packages installed successfully!")
    except subprocess.CalledProcessError:
        print("\n  ERROR: Installation failed.")
        print("  Try running this script with administrator / root privileges,")
        print("  or install manually:  pip install " + " ".join(REQUIRED_PACKAGES))
        sys.exit(1)


def main():
    clear_screen()
    print(BANNER)

    check_python_version()

    print("\n  What would you like to do?")
    print("  1.  Install / upgrade required packages")
    print("  2.  Exit")

    while True:
        choice = input("\n  Choice (1 or 2): ").strip()
        if choice == "1":
            clear_screen()
            print(BANNER)
            install_packages()
            clear_screen()
            print(BANNER)
            print("  All packages installed successfully!\n")
            print("  You're all set! Run Depository.py or MDepository.py to get started.")
            print()
            print("  Tip: Set GITHUB_TOKEN_DEPOSITORY as an environment variable")
            print("  with a GitHub personal access token to raise the API rate")
            print("  limit from 60 to 5,000 requests per hour.")
            input("\n  Press Enter to exit...")
            break
        elif choice == "2":
            print("\n  Goodbye!")
            break
        else:
            print("  Please enter 1 or 2.")


if __name__ == "__main__":
    main()
