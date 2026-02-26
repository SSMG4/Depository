"""
Depository.py  —  Download a single GitHub repository.
Part of the Depository suite by SSMG4.

Usage: python Depository.py
"""

import sys
import time
from depository_core import (
    clear_screen, print_banner, print_token_status, section,
    check_for_update, get_repos, get_branches,
    do_download, prompt_download_method, print_repo_list,
    select_branches, prompt_continue_menu,
    UPDATE_CHECK_INTERVAL, cleanup_pycache,
)


def run():
    current_username = None
    check_for_update()
    last_check = time.time()

    while True:
        # Periodic update re-check
        if time.time() - last_check > UPDATE_CHECK_INTERVAL:
            check_for_update()
            last_check = time.time()

        # ── Username prompt ───────────────────────────────────
        clear_screen()
        print_banner()
        print_token_status()

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
            print_repo_list(repos, username=username)

            print("  Enter repo number:")
            raw = input("  > ").strip()

            if raw.lower() == "back":
                current_username = None
                break  # back to username prompt

            if not raw.isdigit() or not (1 <= int(raw) <= len(repos)):
                print("  Invalid choice.")
                input("  Press Enter to continue...")
                continue

            repo      = repos[int(raw) - 1]
            repo_name = repo["name"]
            desc      = (repo.get("description") or "").strip()

            # ── Fetch branches ────────────────────────────────
            print(f"\n  Fetching branches for '{repo_name}'...")
            branches = get_branches(username, repo_name)
            if branches is None:
                input("  Press Enter to continue...")
                continue
            if not branches:
                print(f"  No branches found for '{repo_name}'.")
                input("  Press Enter to continue...")
                continue

            # ── Branch + method selection ─────────────────────
            clear_screen()
            print_banner()
            section(repo_name)

            selected_branches = select_branches(branches, repo_name,
                                                description=desc)
            if selected_branches is None:
                # User typed 'back' — return to repo list
                continue

            if not selected_branches:
                print("  No valid branches selected.")
                input("  Press Enter to continue...")
                continue

            print()
            use_git = prompt_download_method()

            # ── Download ──────────────────────────────────────
            section("Downloading")
            results = {}
            for branch in selected_branches:
                ok = do_download(username, repo_name, branch, use_git)
                results[branch] = ok

            # ── Summary ───────────────────────────────────────
            clear_screen()
            print_banner()
            section("Download Summary")

            for branch, ok in results.items():
                mark = "[OK]  " if ok else "[FAIL]"
                print(f"  {mark}  {repo_name} [{branch}]")

            ok_count   = sum(1 for v in results.values() if v)
            fail_count = len(results) - ok_count
            print(f"\n  {ok_count} succeeded, {fail_count} failed.")

            # ── Continue? ─────────────────────────────────────
            choice = prompt_continue_menu()
            if choice == "1":
                current_username = username
                break  # stay with same user, re-enter outer loop
            elif choice == "2":
                current_username = None
                break  # different user
            else:
                clear_screen()
                print("\n  Thanks for using Depository! Goodbye.\n")
                cleanup_pycache()
                sys.exit(0)

            break  # exit repo selection loop after a download cycle


if __name__ == "__main__":
    run()
