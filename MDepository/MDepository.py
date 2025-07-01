import os
import requests
from git import Repo, GitCommandError
from tqdm import tqdm
import shutil
import sys
import time
import webbrowser

OUTPUT_DIR = 'output'
UPDATE_CHECK_INTERVAL = 3600  # seconds (1 hour)
UPDATE_CHECK_URL = 'https://api.github.com/repos/SSMG4/Depository/releases/latest'
REMINDER_FILE = os.path.expanduser('~/.mdepository_update_reminder')
IGNORE_FILE = os.path.expanduser('~/.mdepository_ignored_version')


def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')


def print_banner():
    banner = r"""
  ____                       _ _                   
 |  _ \  ___ _ __   ___  ___(_) |_ ___  _ __ _   _ 
 | | | |/ _ \ '_ \ / _ \/ __| | __/ _ \| '__| | | |
 | |_| |  __/ |_) | (_) \__ \ | || (_) | |  | |_| |
 |____/ \___| .__/ \___/|___/_|\__\___/|_|   \__, |
            |_|                              |___/ 

          Your GitHub repo downloader!
    """
    print(banner)


def get_latest_release():
    try:
        resp = requests.get(UPDATE_CHECK_URL, timeout=10)
        if resp.status_code == 200:
            return resp.json()
    except Exception:
        pass
    return None


def should_remind(latest_version):
    if os.path.exists(REMINDER_FILE):
        try:
            with open(REMINDER_FILE, 'r') as f:
                status = f.read().strip()
                if status == 'never':
                    return False
        except:
            pass
    if os.path.exists(IGNORE_FILE):
        try:
            with open(IGNORE_FILE, 'r') as f:
                ignored_version = f.read().strip()
                if ignored_version == latest_version:
                    return False
        except:
            pass
    return True


def set_reminder_status(status):
    try:
        with open(REMINDER_FILE, 'w') as f:
            f.write(status)
    except:
        pass


def ignore_this_version(version):
    try:
        with open(IGNORE_FILE, 'w') as f:
            f.write(version)
    except:
        pass


def check_for_update(current_version):
    release = get_latest_release()
    if not release:
        return

    latest_version = release.get('tag_name') or release.get('name')
    if not latest_version or latest_version == current_version:
        return

    if not should_remind(latest_version):
        return

    print(f"\n🚨 A New Version Of This Tool Is Available: {latest_version} 🚨\n")
    changelog = release.get('body') or "No changelog provided."
    print("Changelog:\n" + changelog + "\n")

    while True:
        print("Options:")
        print("  [y]  Update now")
        print("  [n]  Don't update now")
        print("  [i]  Ignore this version")
        print("  [x]  Never remind me about updates again")
        choice = input("What's your choice?: ").strip().lower()

        if choice == 'y':
            webbrowser.open(release.get('html_url') or "https://github.com/SSMG4/Depository/releases/latest")
            print("Opening your browser to the release page... Exiting tool.")
            sys.exit(0)
        elif choice == 'n':
            print("Got it, I’ll remind you later.")
            set_reminder_status('remind')
            break
        elif choice == 'i':
            print(f"Alright, update {latest_version} will be ignored.")
            ignore_this_version(latest_version)
            break
        elif choice == 'x':
            print("No more update reminders. Enjoy your peace!")
            set_reminder_status('never')
            break
        else:
            print("Please choose from (y/n/i/x).")


def get_repos(username):
    url = f'https://api.github.com/users/{username}/repos'
    resp = requests.get(url)
    if resp.status_code == 404:
        print(f"User '{username}' not found. Please check the username and try again.")
        return None
    if resp.status_code != 200:
        print(f"Error fetching repos: HTTP {resp.status_code}")
        return None
    return resp.json()


def get_branches(username, repo_name):
    url = f'https://api.github.com/repos/{username}/{repo_name}/branches'
    resp = requests.get(url)
    if resp.status_code == 404:
        print(f"Repository '{repo_name}' not found under user '{username}'.")
        return None
    if resp.status_code != 200:
        print(f"Error fetching branches: HTTP {resp.status_code}")
        return None
    return resp.json()


def download_zip(username, repo_name, branch, dest_folder):
    zip_url = f'https://github.com/{username}/{repo_name}/archive/refs/heads/{branch}.zip'
    local_filename = os.path.join(dest_folder, f'{repo_name}-{branch}.zip')
    try:
        with requests.get(zip_url, stream=True) as r:
            if r.status_code != 200:
                print(f"Failed to download ZIP for branch '{branch}' (HTTP {r.status_code})")
                return False
            total_size = int(r.headers.get('content-length', 0))
            with open(local_filename, 'wb') as f, tqdm(
                total=total_size, unit='B', unit_scale=True, desc=f'Downloading {repo_name} [{branch}]'
            ) as pbar:
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        pbar.update(len(chunk))
        return True
    except Exception as e:
        print(f"Error during ZIP download: {e}")
        return False


def clone_branch(username, repo_name, branch, dest_folder):
    repo_url = f'https://github.com/{username}/{repo_name}.git'
    branch_folder = os.path.join(dest_folder, f'{repo_name}-{branch}')
    try:
        if os.path.exists(branch_folder):
            print(f"Branch folder {branch_folder} already exists. Removing it first...")
            shutil.rmtree(branch_folder)
        print(f"Cloning branch '{branch}' of '{repo_name}'...")
        Repo.clone_from(repo_url, branch_folder, branch=branch, depth=1)
        return True
    except GitCommandError as e:
        print(f"Git clone failed: {e}")
        return False
    except Exception as e:
        print(f"Unexpected error during git clone: {e}")
        return False


def prompt_continue_menu():
    print("\nWhat do you want to do next?")
    print("1. Download more repositories from the same user")
    print("2. Return to Main Menu")
    print("3. Exit")
    choice = input("Enter your choice: ").strip()
    while choice not in ('1', '2', '3'):
        print("Invalid choice. Please enter 1, 2 or 3.")
        choice = input("Enter your choice: ").strip()
    return choice


def main_menu():
    clear_screen()
    print_banner()


def main():
    current_username = None
    CURRENT_VERSION = "official-release_v1.1"

    check_for_update(CURRENT_VERSION)
    last_update_check = time.time()

    while True:
        if time.time() - last_update_check > UPDATE_CHECK_INTERVAL:
            check_for_update(CURRENT_VERSION)
            last_update_check = time.time()

        main_menu()
        if current_username is None:
            username = input("Enter GitHub username: ").strip()
        else:
            username = current_username

        repos = get_repos(username)
        if repos is None:
            current_username = None
            input("Press Enter to try again...")
            continue
        if not repos:
            print(f"No repositories found for user '{username}'. Try a different username.")
            current_username = None
            input("Press Enter to continue...")
            continue

        while True:
            clear_screen()
            print_banner()
            print(f"\nRepositories for '{username}':")
            for idx, repo in enumerate(repos, start=1):
                print(f"{idx}. {repo['name']}")
            print(f"\nType 'OK' when you are done selecting repositories.")

            selected_repo_indexes = []
            while True:
                repo_choice = input("Enter repo number to download: ").strip()
                if repo_choice.lower() == 'ok':
                    break
                if not repo_choice.isdigit() or not (1 <= int(repo_choice) <= len(repos)):
                    print("Invalid choice. Please enter a valid repository number or 'OK'.")
                    continue
                idx = int(repo_choice)
                if idx in selected_repo_indexes:
                    print(f"Repository {idx} already selected. Pick another or type 'OK'.")
                else:
                    selected_repo_indexes.append(idx)

            if not selected_repo_indexes:
                print("No repositories selected. Returning to username input.")
                current_username = None
                input("Press Enter to continue...")
                break

            for idx in selected_repo_indexes:
                repo_name = repos[idx - 1]['name']

                branches = get_branches(username, repo_name)
                if branches is None:
                    input("Press Enter to continue...")
                    continue
                if not branches:
                    print(f"No branches found for repository '{repo_name}'.")
                    input("Press Enter to continue...")
                    continue

                clear_screen()
                print_banner()
                print(f"\nBranches for '{repo_name}':")
                for b_idx, branch in enumerate(branches, start=1):
                    print(f"{b_idx}. {branch['name']}")

                print("Enter branch numbers to download separated by commas (or 'all' to download all branches):")
                branch_input = input().strip()
                if branch_input.lower() == 'all':
                    selected_branches = [b['name'] for b in branches]
                else:
                    nums = branch_input.split(',')
                    selected_branches = []
                    for num in nums:
                        num = num.strip()
                        if num.isdigit() and 1 <= int(num) <= len(branches):
                            selected_branches.append(branches[int(num) - 1]['name'])
                        else:
                            print(f"Invalid branch number ignored: {num}")

                if not selected_branches:
                    print("No valid branches selected. Skipping this repository.")
                    input("Press Enter to continue...")
                    continue

                use_git_input = input("Use git to download? (y/n): ").strip().lower()
                while use_git_input not in ('y', 'n'):
                    print("Invalid input. Please enter 'y' or 'n'.")
                    use_git_input = input("Use git to download? (y/n): ").strip().lower()
                use_git = (use_git_input == 'y')

                if not os.path.exists(OUTPUT_DIR):
                    os.makedirs(OUTPUT_DIR)

                for branch in selected_branches:
                    print()
                    if use_git:
                        success = clone_branch(username, repo_name, branch, OUTPUT_DIR)
                    else:
                        success = download_zip(username, repo_name, branch, OUTPUT_DIR)
                    if success:
                        print(f"Downloaded '{repo_name}' [{branch}] successfully.")
                    else:
                        print(f"Failed to download '{repo_name}' [{branch}].")

            while True:
                choice = prompt_continue_menu()
                if choice == '1':
                    current_username = username
                    break
                elif choice == '2':
                    current_username = None
                    break
                elif choice == '3':
                    print("Thanks for using MDepository! Goodbye.")
                    sys.exit(0)

            if choice in ('1', '2'):
                break


if __name__ == "__main__":
    main()
