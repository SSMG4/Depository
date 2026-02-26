# Depository

**A fast, simple CLI tool to download GitHub repositories, single or bulk.**

No more typing `git clone` URLs by hand or fighting GitHub's slow ZIP button. Just run the script, pick a user, pick repos, pick branches, and go.

[![CI Build](https://github.com/SSMG4/Depository/actions/workflows/ci.yml/badge.svg?branch=master)](https://github.com/SSMG4/Depository/actions/workflows/ci.yml)
[![Stars](https://img.shields.io/github/stars/SSMG4/Depository?style=social)](https://github.com/SSMG4/Depository/stargazers)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Issues](https://img.shields.io/github/issues/SSMG4/Depository)](https://github.com/SSMG4/Depository/issues)
[![GitHub all releases](https://img.shields.io/github/downloads/SSMG4/Depository/total?label=Downloads&logo=github)](https://github.com/SSMG4/Depository/releases)
[![Python](https://img.shields.io/badge/-Python-306998?logo=python&logoColor=yellow&style=flat)](https://www.python.org/downloads/)

---

## Features

- Browse and download any public GitHub user's or organization's repositories
- Select individual branches, multiple branches, or all at once
- Choose between **git clone** (shallow, preserves history) or **ZIP download** per repo
- **MDepository** downloads multiple repos concurrently with up to 4 parallel workers
- Full repository listing, fetches every repo, not just the first 30 (paginated API)
- Navigate with `back` at any prompt to return to the previous screen
- Optional GitHub token support to raise the API rate limit from 60 to 5,000 req/hour
- Auto update checker with snooze, ignore, and disable options
- Cleans up `__pycache__` automatically on exit

---

## Versions

| File | Description |
|---|---|
| `Depository.py` | Download one repository at a time |
| `MDepository.py` | Download multiple repositories concurrently |
| `depository_core.py` | Shared library, **required by both, do not delete** |

---

## Requirements

- Python **3.10 or newer**
- `requests`: HTTP client
- `gitpython`: Git operations
- `tqdm`: Progress bars

---

## Installation

### 1. Install dependencies

**Windows:**
```
setup.bat
```

**All platforms:**
```
python setup.py
```

**Or with pip directly:**
```
pip install -r requirements.txt
```

Both setup files verify your Python version and warn if it's too low.

---

### 2. Set a GitHub token (recommended)

Without a token, the GitHub API only allows **60 requests/hour**. With one it's **5,000/hour**, enough for heavy use.

1. Go to [github.com/settings/tokens](https://github.com/settings/tokens) → Generate new token (classic)
2. No scopes needed for public repos — generate and copy it
3. Set it as the `GITHUB_TOKEN_DEPOSITORY` environment variable:

| Platform | Command |
|---|---|
| Windows (current session) | `set GITHUB_TOKEN_DEPOSITORY=your_token_here` |
| Windows (permanent, PowerShell) | `[System.Environment]::SetEnvironmentVariable("GITHUB_TOKEN_DEPOSITORY", "your_token_here", "User")` |
| macOS / Linux (current session) | `export GITHUB_TOKEN_DEPOSITORY=your_token_here` |
| macOS / Linux (permanent) | Add the `export` line to `~/.bashrc` or `~/.zshrc` |

---

### 3. Run

```
python Depository.py
```
```
python MDepository.py
```

---

## Usage

1. Enter a GitHub **username** or **organization name**
2. Pick a **repository** from the numbered list
   - In MDepository, select multiple repos (e.g. `1,3,7`) or type `all`
3. Pick **branches**, enter numbers separated by commas, type `all`, or `back` to return
4. Choose your **download method**: `g` for git clone, `z` for ZIP
   - In MDepository you can apply one method to all repos, or choose per repo
5. Files are saved to the `output/` folder next to the script

At any selection prompt, typing `back` returns you to the previous screen.

---

## Project Structure

```
Depository/
├── Depository.py          # Single-repo downloader
├── MDepository.py         # Multi-repo concurrent downloader
├── depository_core.py     # Shared library (API, download, UI helpers)
├── setup.py               # Python dependency installer
├── setup.bat              # Windows batch dependency installer
├── requirements.txt       # Pip requirements
├── .github/
│   └── workflows/
│       └── ci.yml         # CI pipeline
├── .gitignore
├── .gitattributes
└── README.md
```

---

## FAQ

**Do I need Git installed?**
Only if you choose the `git clone` download method. ZIP downloads work without Git.

**Can I download private repositories?**
No, the tool only uses the public GitHub API.

**Why does `__pycache__` appear and disappear?**
Python generates it automatically when importing modules. Depository removes it on every clean exit (every exit made via the tool's options). Force-closing the terminal skips cleanup, this is a Python/OS limitation.

**Is this safe?**
The source is fully open, read it yourself, or run the files through [VirusTotal](https://www.virustotal.com).

---

## License

[MIT License](LICENSE)

&copy; 2026 SSMG4 All Rights Reserved.
