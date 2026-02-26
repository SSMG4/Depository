"""
MDepository.py  —  Download multiple GitHub repositories concurrently.
Part of the Depository suite by SSMG4.

Usage: python MDepository.py
"""

import sys
import time
import os
from concurrent.futures import ThreadPoolExecutor, as_completed

from depository_core import (
    clear_screen, print_banner, print_token_status, section,
    check_for_update, get_repos, get_branches,
    do_download, prompt_download_method, print_repo_list,
    select_branches, prompt_continue_menu,
    UPDATE_CHECK_INTERVAL, OUTPUT_DIR, cleanup_pycache,
)

MAX_WORKERS = 4  # Concurrent downloads


# ──────────────────────────────────────────────────────────────────────────────
# Repo selection
# ──────────────────────────────────────────────────────────────────────────────

def select_repos(repos: list, username: str = "") -> list[int] | None:
    """
    Returns a list of 0-based indexes, or None if the user types 'back'.
    """
    print_repo_list(repos, username=username)
    print("  Enter repo numbers separated by commas, or 'all':")
    raw = input("  > ").strip()

    if raw.lower() == "back":
        return None

    if raw.lower() == "all":
        return list(range(len(repos)))

    indexes = []
    for token in raw.split(","):
        token = token.strip()
        if token.isdigit() and 1 <= int(token) <= len(repos):
            idx = int(token) - 1
            if idx not in indexes:
                indexes.append(idx)
        else:
            print(f"  Skipping invalid entry: '{token}'")
    return indexes


# ──────────────────────────────────────────────────────────────────────────────
# Method strategy
# ──────────────────────────────────────────────────────────────────────────────

def ask_method_strategy() -> str:
    """Returns 'same' or 'per'."""
    print()
    print("  Download method:")
    print("  1.  Same method for all repositories")
    print("  2.  Choose per repository")
    while True:
        choice = input("  Choice (1/2): ").strip()
        if choice == "1":
            return "same"
        if choice == "2":
            return "per"
        print("  Please enter 1 or 2.")


# ──────────────────────────────────────────────────────────────────────────────
# Branch + method config per repo
# ──────────────────────────────────────────────────────────────────────────────

def build_download_jobs(username: str, selected_repos: list[dict],
                        method_strategy: str,
                        global_use_git: bool | None) -> list[tuple] | None:
    """
    For each selected repo, show its info and let the user pick branches.
    Returns a list of (username, repo_name, branch, use_git) tuples,
    or None if the user types 'back' during any repo's branch selection
    (signals: go back to repo selection).
    """
    jobs = []

    for i, repo in enumerate(selected_repos, 1):
        repo_name = repo["name"]
        desc      = (repo.get("description") or "").strip()

        clear_screen()
        print_banner()
        section(f"Repo {i} of {len(selected_repos)}: {repo_name}")

        print(f"  Fetching branches...")
        branches = get_branches(username, repo_name)
        if branches is None or not branches:
            print(f"  Could not fetch branches for '{repo_name}'. Skipping.")
            input("  Press Enter to continue...")
            continue

        clear_screen()
        print_banner()
        section(f"Repo {i} of {len(selected_repos)}: {repo_name}")

        selected_branches = select_branches(branches, repo_name,
                                            description=desc)
        if selected_branches is None:
            # User typed 'back' — abort job building entirely
            return None

        if not selected_branches:
            print(f"  No branches selected for '{repo_name}'. Skipping.")
            input("  Press Enter to continue...")
            continue

        if method_strategy == "per":
            print()
            use_git = prompt_download_method()
        else:
            use_git = global_use_git

        for branch in selected_branches:
            jobs.append((username, repo_name, branch, use_git))

    return jobs


# ──────────────────────────────────────────────────────────────────────────────
# Concurrent downloader
# ──────────────────────────────────────────────────────────────────────────────

def run_downloads(jobs: list[tuple]) -> dict[tuple, bool]:
    results = {}
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    clear_screen()
    print_banner()
    section("Downloading")
    print(f"  {len(jobs)} download(s) queued  —  up to {MAX_WORKERS} running at once\n")

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
        future_to_job = {
            pool.submit(do_download, user, repo, branch, use_git): (repo, branch)
            for user, repo, branch, use_git in jobs
        }
        for future in as_completed(future_to_job):
            repo_name, branch = future_to_job[future]
            try:
                ok = future.result()
            except Exception as exc:
                print(f"  [x]  {repo_name} [{branch}] — exception: {exc}")
                ok = False
            results[(repo_name, branch)] = ok

    return results


# ──────────────────────────────────────────────────────────────────────────────
# Main loop
# ──────────────────────────────────────────────────────────────────────────────

def run():
    current_username = None
    check_for_update()
    last_check = time.time()

    while True:
        if time.time() - last_check > UPDATE_CHECK_INTERVAL:
            check_for_update()
            last_check = time.time()

        # ── Username prompt ───────────────────────────────────
        clear_screen()
        print_banner()
        print_token_status()
        print("  Mode: Multiple Repository Download\n")

        if current_username:
            username = current_username
            print(f"  User: {username}\n")
        else:
            username = input("  GitHub username: ").strip()
            if not username:
                continue

        # ── Fetch repos ───────────────────────────────────────
        print(f"\n  Fetching repositories for '{username}'...")
        repos = get_repos(username)
        if repos is None:
            current_username = None
            input("\n  Press Enter to try again...")
            continue
        if not repos:
            print(f"\n  No public repositories found for '{username}'.")
            current_username = None
            input("  Press Enter to continue...")
            continue

        # ── Repo selection loop ───────────────────────────────
        while True:
            clear_screen()
            print_banner()
            repo_indexes = select_repos(repos, username=username)

            if repo_indexes is None:
                # User typed 'back' — return to username prompt
                current_username = None
                break

            if not repo_indexes:
                print("\n  No repositories selected.")
                input("  Press Enter to continue...")
                continue

            selected_repos_list = [repos[i] for i in repo_indexes]

            # ── Method strategy ───────────────────────────────
            method_strategy = ask_method_strategy()
            global_use_git: bool | None = None
            if method_strategy == "same":
                print()
                global_use_git = prompt_download_method()

            # ── Per-repo branch config ────────────────────────
            jobs = build_download_jobs(username, selected_repos_list,
                                       method_strategy, global_use_git)

            if jobs is None:
                # User typed 'back' during branch selection — re-show repo list
                continue

            if not jobs:
                print("\n  No valid download jobs queued.")
                input("  Press Enter to continue...")
                continue

            # ── Run downloads ─────────────────────────────────
            results = run_downloads(jobs)

            # ── Summary ───────────────────────────────────────
            clear_screen()
            print_banner()
            section("Download Summary")

            ok_count   = sum(1 for v in results.values() if v)
            fail_count = len(results) - ok_count

            for (repo_name, branch), ok in sorted(results.items()):
                mark = "[OK]  " if ok else "[FAIL]"
                print(f"  {mark}  {repo_name} [{branch}]")

            print(f"\n  {ok_count} succeeded, {fail_count} failed.")

            # ── Continue? ─────────────────────────────────────
            choice = prompt_continue_menu()
            if choice == "1":
                current_username = username
                break  # re-enter outer loop with same user
            elif choice == "2":
                current_username = None
                break  # different user
            else:
                clear_screen()
                print("\n  Thanks for using MDepository! Goodbye.\n")
                cleanup_pycache()
                sys.exit(0)

            break  # exit repo selection loop after a download cycle


if __name__ == "__main__":
    run()
