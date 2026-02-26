"""
depository_core.py
Shared utilities for Depository and MDepository.
"""

import os
import sys
import stat
import shutil
import atexit
import requests
import webbrowser
from git import Repo, GitCommandError
from tqdm import tqdm

# ──────────────────────────────────────────────
# Constants
# ──────────────────────────────────────────────

OUTPUT_DIR = "output"
UPDATE_CHECK_URL = "https://api.github.com/repos/SSMG4/Depository/releases/latest"
CURRENT_VERSION = "official-release_v2.0"
UPDATE_CHECK_INTERVAL = 3600  # seconds (1 hour)

# Optional GitHub personal access token.
# Get one at: https://github.com/settings/tokens  (no scopes needed for public repos)
_GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN_DEPOSITORY", "").strip()

REMINDER_FILE = os.path.expanduser("~/.depository_update_reminder")
IGNORE_FILE   = os.path.expanduser("~/.depository_ignored_version")

# ──────────────────────────────────────────────
# __pycache__ cleanup
# ──────────────────────────────────────────────

def cleanup_pycache():
    """Remove __pycache__ folders next to the scripts."""
    base = os.path.dirname(os.path.abspath(__file__))
    for root, dirs, _ in os.walk(base):
        for d in dirs:
            if d == "__pycache__":
                target = os.path.join(root, d)
                try:
                    shutil.rmtree(target, onerror=_force_remove_readonly)
                except OSError:
                    pass

atexit.register(cleanup_pycache)

# ──────────────────────────────────────────────
# Internal helpers
# ──────────────────────────────────────────────

def _force_remove_readonly(func, path, _):
    """onerror handler for shutil.rmtree — strips read-only on Windows then retries."""
    try:
        os.chmod(path, stat.S_IWRITE)
        func(path)
    except Exception:
        pass


def _auth_headers() -> dict:
    if _GITHUB_TOKEN:
        return {"Authorization": f"Bearer {_GITHUB_TOKEN}"}
    return {}


def _get(url: str, **kwargs) -> requests.Response:
    return requests.get(url, headers=_auth_headers(), timeout=15, **kwargs)


# ──────────────────────────────────────────────
# UI helpers
# ──────────────────────────────────────────────

def clear_screen():
    os.system("cls" if os.name == "nt" else "clear")


BANNER = r"""
  ____                       _ _                   
 |  _ \  ___ _ __   ___  ___(_) |_ ___  _ __ _   _ 
 | | | |/ _ \ '_ \ / _ \/ __| | __/ _ \| '__| | | |
 | |_| |  __/ |_) | (_) \__ \ | || (_) | |  | |_| |
 |____/ \___| .__/ \___/|___/_|\__\___/|_|   \__, |
            |_|                              |___/ 

          Your GitHub repository downloader!
"""


def print_banner():
    print(BANNER)


def print_token_status():
    if _GITHUB_TOKEN:
        print("  [TOKEN]  GitHub token active — 5,000 req/hour limit.\n")
    else:
        print("  [!]  No GITHUB_TOKEN_DEPOSITORY set — limit is 60 req/hour.")
        print("       Set GITHUB_TOKEN_DEPOSITORY to raise it to 5,000/hour.\n")


def section(title: str = ""):
    """Print a divider, optionally with a title."""
    width = 56
    if title:
        pad = width - len(title) - 2
        left = pad // 2
        right = pad - left
        print(f"\n  {'─' * left} {title} {'─' * right}\n")
    else:
        print(f"\n  {'─' * width}\n")


# ──────────────────────────────────────────────
# Update checker
# ──────────────────────────────────────────────

def _get_latest_release() -> dict | None:
    try:
        resp = _get(UPDATE_CHECK_URL)
        if resp.status_code == 200:
            return resp.json()
    except Exception:
        pass
    return None


def _should_remind(latest_version: str) -> bool:
    for path in (REMINDER_FILE, IGNORE_FILE):
        if os.path.exists(path):
            try:
                with open(path) as f:
                    val = f.read().strip()
                if path == REMINDER_FILE and val == "never":
                    return False
                if path == IGNORE_FILE and val == latest_version:
                    return False
            except OSError:
                pass
    return True


def _write_file(path: str, content: str):
    try:
        with open(path, "w") as f:
            f.write(content)
    except OSError:
        pass


def check_for_update():
    release = _get_latest_release()
    if not release:
        return
    latest = release.get("tag_name") or release.get("name", "")
    if not latest or latest == CURRENT_VERSION:
        return
    if not _should_remind(latest):
        return

    print(f"\n  [!]  New version available: {latest}  (you have {CURRENT_VERSION})\n")
    changelog = (release.get("body") or "No changelog provided.").strip()
    print(f"  Changelog:\n  {changelog}\n")

    while True:
        print("  [y]  Open release page in browser")
        print("  [n]  Remind me later")
        print("  [i]  Ignore this version")
        print("  [x]  Never remind me again")
        choice = input("\n  Choice: ").strip().lower()
        if choice == "y":
            webbrowser.open(release.get("html_url") or
                            "https://github.com/SSMG4/Depository/releases/latest")
            print("  Opening browser...")
            cleanup_pycache()
            sys.exit(0)
        elif choice == "n":
            _write_file(REMINDER_FILE, "remind")
            break
        elif choice == "i":
            _write_file(IGNORE_FILE, latest)
            print(f"  Version {latest} will be ignored.")
            break
        elif choice == "x":
            _write_file(REMINDER_FILE, "never")
            print("  Update reminders disabled.")
            break
        else:
            print("  Please enter y, n, i, or x.")


# ──────────────────────────────────────────────
# GitHub API
# ──────────────────────────────────────────────

def get_repos(username: str) -> list | None:
    """Return ALL public repos for a GitHub user/org (handles pagination)."""
    repos = []
    page = 1
    while True:
        url = (f"https://api.github.com/users/{username}/repos"
               f"?per_page=100&page={page}")
        try:
            resp = _get(url)
        except requests.RequestException as exc:
            print(f"  Network error: {exc}")
            return None

        if resp.status_code == 404:
            print(f"  User '{username}' not found.")
            return None
        if resp.status_code == 403:
            print("  API rate limit reached. Set GITHUB_TOKEN_DEPOSITORY to "
                  "raise the limit to 5,000 requests/hour.")
            return None
        if resp.status_code != 200:
            print(f"  Unexpected API error: HTTP {resp.status_code}")
            return None

        page_data = resp.json()
        if not page_data:
            break
        repos.extend(page_data)
        if len(page_data) < 100:
            break
        page += 1

    return repos


def get_branches(username: str, repo_name: str) -> list | None:
    """Return all branches for a repository."""
    branches = []
    page = 1
    while True:
        url = (f"https://api.github.com/repos/{username}/{repo_name}/branches"
               f"?per_page=100&page={page}")
        try:
            resp = _get(url)
        except requests.RequestException as exc:
            print(f"  Network error: {exc}")
            return None

        if resp.status_code == 404:
            print(f"  Repository '{repo_name}' not found under '{username}'.")
            return None
        if resp.status_code == 403:
            print("  API rate limit reached.")
            return None
        if resp.status_code != 200:
            print(f"  Unexpected API error: HTTP {resp.status_code}")
            return None

        page_data = resp.json()
        if not page_data:
            break
        branches.extend(page_data)
        if len(page_data) < 100:
            break
        page += 1

    return branches


# ──────────────────────────────────────────────
# Download functions
# ──────────────────────────────────────────────

def download_zip(username: str, repo_name: str, branch: str,
                 dest_folder: str) -> bool:
    zip_url = (f"https://github.com/{username}/{repo_name}"
               f"/archive/refs/heads/{branch}.zip")
    local_path = os.path.join(dest_folder, f"{repo_name}-{branch}.zip")
    try:
        with _get(zip_url, stream=True) as r:
            if r.status_code != 200:
                print(f"  [x]  ZIP download failed for '{branch}' (HTTP {r.status_code})")
                return False
            total = int(r.headers.get("content-length", 0))
            with open(local_path, "wb") as f, tqdm(
                total=total, unit="B", unit_scale=True,
                desc=f"  {repo_name} [{branch}]", leave=True
            ) as bar:
                for chunk in r.iter_content(chunk_size=65536):
                    if chunk:
                        f.write(chunk)
                        bar.update(len(chunk))
        return True
    except Exception as exc:
        print(f"  [x]  Error during ZIP download: {exc}")
        return False


def clone_branch(username: str, repo_name: str, branch: str,
                 dest_folder: str) -> bool:
    repo_url = f"https://github.com/{username}/{repo_name}.git"
    branch_folder = os.path.join(dest_folder, f"{repo_name}-{branch}")
    try:
        if os.path.exists(branch_folder):
            shutil.rmtree(branch_folder, onerror=_force_remove_readonly)
        print(f"  Cloning {repo_name} [{branch}]...")
        Repo.clone_from(repo_url, branch_folder, branch=branch, depth=1)
        return True
    except GitCommandError as exc:
        print(f"  [x]  Git clone failed: {exc}")
        return False
    except Exception as exc:
        print(f"  [x]  Unexpected error: {exc}")
        return False


def do_download(username: str, repo_name: str, branch: str,
                use_git: bool) -> bool:
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    if use_git:
        return clone_branch(username, repo_name, branch, OUTPUT_DIR)
    return download_zip(username, repo_name, branch, OUTPUT_DIR)


# ──────────────────────────────────────────────
# Shared input helpers
# ──────────────────────────────────────────────

def prompt_download_method() -> bool:
    """Ask the user whether to use git clone or ZIP. Returns True for git."""
    while True:
        choice = input("  Download via git clone or zip? (g/z): ").strip().lower()
        if choice in ("g", "git"):
            return True
        if choice in ("z", "zip"):
            return False
        print("  Please enter 'g' or 'z'.")


def print_repo_list(repos: list, username: str = ""):
    """Print a clean numbered repository list."""
    header = f"  Repositories for '{username}'" if username else "  Repositories"
    print(f"{header}  ({len(repos)} total)\n")
    for idx, repo in enumerate(repos, 1):
        print(f"  {idx:<4} {repo['name']}")
    print()
    print("  Type 'back' to return to the main menu.")
    print()


def select_branches(branches: list, repo_name: str = "",
                    description: str = "") -> list[str] | None:
    """
    Interactive branch selector.
    Returns a list of branch name strings, or None if the user types 'back'.
    """
    if description:
        print(f"  {description}\n")

    label = f" for '{repo_name}'" if repo_name else ""
    print(f"  Branches{label}:")
    for idx, b in enumerate(branches, 1):
        print(f"    {idx}. {b['name']}")

    print("\n  Enter branch numbers separated by commas, 'all', or 'back':")
    raw = input("  > ").strip()

    if raw.lower() == "back":
        return None

    if raw.lower() == "all":
        return [b["name"] for b in branches]

    selected = []
    for token in raw.split(","):
        token = token.strip()
        if token.isdigit() and 1 <= int(token) <= len(branches):
            name = branches[int(token) - 1]["name"]
            if name not in selected:
                selected.append(name)
        else:
            print(f"  Skipping invalid entry: '{token}'")
    return selected


def prompt_continue_menu() -> str:
    """Return '1' (same user), '2' (main menu), or '3' (exit)."""
    section("What next?")
    print("  1.  Download more repos from the same user")
    print("  2.  Return to main menu  (different user)")
    print("  3.  Exit")
    print()
    while True:
        choice = input("  Choice: ").strip()
        if choice in ("1", "2", "3"):
            return choice
        print("  Please enter 1, 2, or 3.")
