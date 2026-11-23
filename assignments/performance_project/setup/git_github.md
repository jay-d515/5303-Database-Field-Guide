# Git & GitHub

Two folders on your machine, but only one repo is yours:

| Folder                        | What it is                                          | You…                                         |
| ----------------------------- | --------------------------------------------------- | -------------------------------------------- |
| **5303-Database-Field-Guide** | the course materials (a clone, not your repo)       | clone it, `git pull` for updates, never edit |
| **your course repo**          | one folder per assignment, including `Performance_Project/` | commit, push                           |

Use the course repo you already submit your other assignments from. This
project doesn't need a repo of its own: it's one more folder in that one.

Keeping your work out of the field guide clone means `git pull` always
succeeds: there are no edits of yours for an update to collide with.

## 1. Install Git

| OS      | Install                                                                 |
| ------- | ----------------------------------------------------------------------- |
| macOS   | `xcode-select --install` (or `brew install git`)                        |
| Windows | [git-scm.com](https://git-scm.com/download/win). Keep the defaults; it includes **Git Bash**. |
| Linux   | `sudo apt install git` (or your distribution's package manager)        |

Tell Git who you are, once per machine:

```bash
git config --global user.name  "Your Name"
git config --global user.email "you@example.com"    # the email on your GitHub account
git config --global init.defaultBranch main
```

## 2. Connect to GitHub

Create a free account at [github.com](https://github.com) if you don't have
one. Then let your machine push to it. The easiest way is the GitHub CLI:

```bash
# macOS: brew install gh      Windows: winget install GitHub.cli
gh auth login                  # choose GitHub.com, HTTPS, and "Login with a web browser"
```

## 3. Clone the field guide

```bash
mkdir -p ~/5303 && cd ~/5303
git clone https://github.com/rugbyprof/5303-Database-Field-Guide.git
```

When materials are updated:

```bash
cd ~/5303/5303-Database-Field-Guide
git pull
```

If `git pull` complains about local changes, you edited something in the
clone. `git stash` sets your edits aside, and `git pull` will then work.
Move anything you want to keep into your course repo.

## 4. Add the project folder to your course repo

Your course repo holds every assignment, one folder each, at the top level.
The examples below call it `~/5303/my-repo`; use your repo's real name and
location. If you don't have it on this machine yet, clone it next to the
field guide:

```bash
cd ~/5303
git clone https://github.com/<your-username>/<your-repo>.git my-repo
```

Make sure your instructor can see it (if they ask you to, add them as a
collaborator under **Settings → Collaborators** on GitHub).

This project's work goes in `Performance_Project/`, laid out one folder per
unit:

```
my-repo/
├── Caching_Project/             (other assignments sit beside it)
├── Standardizing_Api_Responses/
└── Performance_Project/
    ├── README.md
    ├── sqlite/
    │   ├── FINDINGS_sqlite.md
    │   ├── my_schema.sql
    │   └── your_turn_checks.sql
    ├── duckdb/
    └── api/                     your copy of lab/api/starter_code (see below)
```

### Working on files that come from the field guide

Some files start in the field guide and become yours once you fill them in,
like [your_turn_checks.sql](../engines/01_sqlite/04_model/your_turn_checks.sql).
Copy them into `Performance_Project/` in your repo and edit the copy.

**The API starter code** works from a copy too. Tell it where the field
guide's `Performance_Project` folder is, and it finds the SQL files there:

```bash
mkdir -p ~/5303/my-repo/Performance_Project
cp -R ~/5303/5303-Database-Field-Guide/assignments/Performance_Project/lab/api/starter_code \
      ~/5303/my-repo/Performance_Project/api
export FIELD_GUIDE="$HOME/5303/5303-Database-Field-Guide/assignments/Performance_Project"   # add to ~/.zshrc or ~/.bashrc
```

## 5. The everyday loop

```bash
cd ~/5303/my-repo
git add Performance_Project
git commit -m "Performance SQLite 07: driver results and plan summaries"
git push
```

Commit when something works, not once at the end. A history of small
commits is a record of your progress, and a safety net when something
breaks.

## Check

```bash
git --version
cd ~/5303/5303-Database-Field-Guide && git pull     # "Already up to date."
cd ~/5303/my-repo && git status                     # "On branch main"
```

Then open your course repo on github.com and confirm `Performance_Project/`
is there.
