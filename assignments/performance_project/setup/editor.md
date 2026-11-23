# Editor

Any editor works. The course examples assume **VS Code**, because it handles
Python, SQL, Markdown, and Docker in one place, and it's free.

## 1. Install

Download from [code.visualstudio.com](https://code.visualstudio.com/). On
macOS, open the Command Palette (**⇧⌘P**) and run **Shell Command: Install
'code' command in PATH**, so `code .` opens a folder from the terminal.

## 2. Extensions

Install from the Extensions view (**⇧⌘X** / **Ctrl+Shift+X**):

| Extension                         | ID                           | Why                                                            |
| --------------------------------- | ---------------------------- | -------------------------------------------------------------- |
| Python                            | `ms-python.python`           | Runs and debugs Python, picks the venv, includes Pylance       |
| Markdown Preview Mermaid Support  | `bierner.markdown-mermaid`   | Renders the diagrams in the field guide's Markdown             |
| Docker                            | `ms-azuretools.vscode-docker` | See and manage containers (from unit 03)                      |
| SQLite Viewer *(optional)*        | `qwtel.sqlite-viewer`        | Browse a `.db` file's tables without leaving the editor        |

From the terminal instead:

```bash
code --install-extension ms-python.python
code --install-extension bierner.markdown-mermaid
code --install-extension ms-azuretools.vscode-docker
```

## 3. Open the right folder

Open **the folder you're working in**, not your home folder:

```bash
code ~/5303/my-repo/Performance_Project/api
```

Then pick the project's venv: Command Palette → **Python: Select
Interpreter** → `./.venv`. VS Code remembers it for that folder.

## 4. Two settings that save trouble

- **Don't let "organize imports" rewrite the API's imports.** The `app/`
  package uses relative imports (`from .experiment import run_query`).
  Rewritten as `from experiment import ...`, they look fine in the editor
  but crash at runtime.
- **Markdown preview:** **⇧⌘V** / **Ctrl+Shift+V** opens the rendered view
  of a README, tables and diagrams included.

## Check

Open the field guide (`code ~/5303/5303-Database-Field-Guide`), open
[engines/01_sqlite/04_model/README.md](../engines/01_sqlite/04_model/README.md),
and preview it. The schema diagram in section A4 should render as a
diagram, not as text.
