# Python

The course needs **Python 3.11 or newer**: the measurement API, the data
generators, and the drivers for every engine run on it.

## 1. Install it

| OS      | Install                                                                                                  |
| ------- | -------------------------------------------------------------------------------------------------------- |
| macOS   | [python.org](https://www.python.org/downloads/) installer, or `brew install python@3.13`                 |
| Windows | [python.org](https://www.python.org/downloads/) installer. **Check "Add python.exe to PATH"** on the first screen. |
| Linux   | your package manager, e.g. `sudo apt install python3 python3-venv`                                       |

Check it:

```bash
python3 --version        # macOS / Linux: 3.11 or higher
py --version             # Windows
```

> **macOS:** the `python3` that comes with the Xcode tools may be older than
> 3.11. If `python3 --version` says 3.9, install from python.org or Homebrew,
> then open a new terminal.

## 2. Virtual environments: one per project

A **virtual environment** (venv) is a private folder of packages for one
project. The API's FastAPI version can't clash with another class's, and
deleting the folder undoes everything.

```bash
cd ~/5303/my-repo/Performance_Project/api
python3 -m venv .venv                 # Windows: py -m venv .venv
source .venv/bin/activate             # Windows: .venv\Scripts\activate
```

Your prompt now starts with `(.venv)`. While it does, `python` and `pip`
mean *this project's* copies.

```bash
pip install -e ".[dev]"               # install what pyproject.toml lists
deactivate                            # leave the venv
```

**Rules of thumb:**

- One `.venv` per project folder, created inside it. It's git-ignored, never
  committed.
- If something is badly broken, delete `.venv` and create it again. That's
  normal, not a failure.
- Activate the venv in **every new terminal** before running the project.

## 3. pipx: Python command-line tools

`pipx` installs a Python **tool** (like QueryMux) into its own hidden
environment and puts the command on your `PATH`, so it works from any
folder without activating anything.

```bash
python3 -m pip install --user pipx    # Windows: py -m pip install --user pipx
python3 -m pipx ensurepath            # then open a new terminal
```

Use `pip` inside a venv for a project's libraries, and `pipx` for tools you
run as commands.

## Check

```bash
python3 --version                     # 3.11+
python3 -m venv /tmp/venvtest && echo "venv works"
pipx --version
```
