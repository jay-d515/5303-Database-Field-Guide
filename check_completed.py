#!/usr/bin/env python3
"""Check your assignment folders against the examples in completed/.

The field guide's completed/ folder shows what each finished assignment folder
should contain. This script compares YOUR folders with it, file by file, and
looks inside each file for work of your own: a .py file must hold Python code,
a .md file must hold writing in Markdown, a .sql file must hold SQL, a .csv
must hold data rows, and so on. It checks that the work is there, not that it
is right. A clean run means "nothing obvious is missing", not "full marks".

Usage (from your course repo, the one with a folder per assignment):
    python ~/5303/5303-Database-Field-Guide/check_completed.py              # every assignment folder found
    python ~/5303/5303-Database-Field-Guide/check_completed.py caching      # one assignment (a prefix is enough)
    python ~/5303/5303-Database-Field-Guide/check_completed.py perf stand   # several
    python ~/5303/5303-Database-Field-Guide/check_completed.py --repo ~/5303/my-repo

Run it from inside one assignment folder and it checks just that one.

Every row gets one of:
    ✅  found, with work of your own in it
    🟡  found, but worth a look (a warning: it doesn't fail the run)
    ❌  missing, or still just the template
    ⚪  optional, and not there (that's fine)

The exit code is 0 when nothing is ❌, 1 otherwise.

Names are matched without regard to capitalization (caching_project counts as
Caching_Project), and the variations listed in each completed/<assignment>/
README.md are accepted under their own names. Text you copied from a template
or starter file doesn't count as your own: only what you added does.
"""

import argparse
import ast
import csv
import fnmatch
import io
import json
import os
import re
import subprocess
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:  # Python older than 3.11
    tomllib = None

ROOT = Path(__file__).resolve().parent
COMPLETED = ROOT / 'completed'

OK, WARN, BAD, SKIP = '✅', '🟡', '❌', '⚪'

# Skipped when reading your folder (they're never part of the work)
SKIP_DIRS = ('.git', '.venv', 'venv', '__pycache__', '.pytest_cache',
             '.ipynb_checkpoints', 'node_modules', '*.egg-info')
# Reported when git would commit them
JUNK_DIRS = ('.venv', 'venv', '__pycache__', '.pytest_cache', '.ipynb_checkpoints', '*.egg-info')
JUNK_FILES = ('*.db', '*.db-wal', '*.db-shm', '*.db-journal', '*.sqlite', '*.sqlite3',
              '*.duckdb', '*.duckdb.wal', '*.parquet', 'dump.rdb', '.env', '.DS_Store')

IMAGES = ('*.png', '*.jpg', '*.jpeg', '*.gif', '*.svg', '*.webp', '*.pdf')


# ================================================================ the rules

@dataclass
class Rule:
    """How to judge one entry of a completed/ folder.

    Every file in completed/<assignment>/ is required unless a rule says
    otherwise. Paths are relative to the assignment folder; any of them may be
    a glob ('tests/test_*.py').
    """
    need: str = 'required'      # 'required', 'recommended', or 'optional'
    alts: tuple = ()            # other names that count (the README's variations)
    baseline: tuple = ()        # field-guide files you start from: their text isn't yours
    copied: bool = False        # meant to be an unchanged copy: only check it's real
    min_words: int = None       # .md / .txt: words of your own
    min_code: int = None        # .py: statements;  .sql: statements
    blanks: str = None          # regex for prompt lines you must fill in
    leftovers: tuple = ()       # template text that should be gone by now
    hints: tuple = ()           # (regex, message): content you'd expect to see
    todo: bool = False          # warn while '# TODO' markers remain
    fallback: tuple = None      # (file, regex): may live inside another file instead
    folder_has: tuple = ()      # a folder that must hold a file matching one of these
    any_of: tuple = ()          # at least one of these paths must exist
    csv_distinct: tuple = None  # (column, how many distinct values, message)
    generated: bool = False     # written by a program (driver output), not by you
    must_change: bool = False   # .html: unchanged from its starter is a failure, not a warning


def section(n, words):
    """Heading regex for 'Section n' of a unit, e.g. '## §1 Why it exists'."""
    return rf'§\s*0?{n}\b|\b0{n}[_ ]|{words}'


FINDINGS_TEMPLATE = 'assignments/performance_project/lab/findings_template.md'
STARTER = 'assignments/performance_project/lab/api/starter_code'

SPEC = {
    'Caching_Project': {
        'README.md': Rule(min_words=400, hints=(
            (r'\|.*\|.*\|', 'no results table'),
            (r'!\[[^\]]*\]\([^)]+\)|\.(png|svg|jpe?g)\b', 'no graph embedded or linked'),
            (r'(?i)p95', 'p95 latency is never mentioned'),
        )),
        'requirements.txt': Rule(alts=('requirements*.txt', 'pyproject.toml'), hints=(
            (r'(?im)^\s*"?fastapi', 'fastapi is not listed'),
            (r'(?im)^\s*"?redis', 'redis is not listed'),
            (r'(?im)^\s*"?uvicorn', 'uvicorn is not listed'),
        )),
        'setup_db.py': Rule(min_code=5, hints=(
            (r'(?i)create\s+table', 'no CREATE TABLE'),
        )),
        'main.py': Rule(alts=('app/main.py', 'app.py', 'api.py', 'app/api.py'), min_code=10, hints=(
            (r'(?m)^\s*(import|from)\s+redis', "doesn't import redis"),
            (r'setex|\bex\s*=|expire', 'no TTL set on a cached value'),
            (r'FastAPI', 'no FastAPI app'),
        )),
        'benchmark.py': Rule(alts=('benchmark*.py', 'bench*.py', '*benchmark*.sh', 'locustfile.py',
                                   'load_test*.js', 'k6*.js', '*.ipynb'), min_code=5),
        'make_graphs.py': Rule(need='recommended', alts=('*graph*.py', '*plot*.py', '*chart*.py', '*.ipynb')),
        '.gitignore': Rule(need='optional'),
        'results/part_a_baseline.csv': Rule(need='optional'),
        'results/part_b_redis.csv': Rule(need='optional'),
        'results/part_c_ttl.csv': Rule(need='optional'),
        'results/part_d_dict_vs_redis.csv': Rule(need='optional'),
        'results/part_e_query_complexity.csv': Rule(need='optional'),
        'results/': Rule(alts=('data/', 'output/', 'benchmarks/', 'benchmark_results/'),
                         folder_has=('*.csv', '*.json', '*.txt', '*.md')),
        'graphs/': Rule(alts=('figures/', 'images/', 'plots/', 'img/', 'charts/'), folder_has=IMAGES),
        'extension/README.md': Rule(need='optional', min_words=60),
        'extension/stampede.py': Rule(need='optional', min_code=5),
    },

    'Standardizing_Api_Responses': {
        'README.md': Rule(min_words=250, hints=(
            (r'total_size', '`total_size` is never mentioned'),
            (r'(?i)postgres', 'the PostgreSQL question is not answered'),
            (r'(?i)index\.html|client', 'no client-side changes section'),
        )),
        'api.py': Rule(alts=('app/api.py', 'main.py', 'app/main.py'), baseline=('lessons/*/api.py',),
                       min_code=20, hints=(
            (r'\boffset\b', 'no offset parameter (Part 3)'),
            (r'exception_handler', 'no exception handlers registered (Part 5)'),
            (r'RequestValidationError', 'RequestValidationError is not handled (the 422 errors)'),
        )),
        'responses.py': Rule(alts=('response.py', 'envelope.py', 'api_response.py', 'responses/*.py',
                                   '*/responses.py', '*/response.py', 'schemas.py', '*/schemas.py',
                                   'models.py', '*/models.py'),
                             fallback=('api.py', r'total_size'), hints=(
            (r'total_size', 'no total_size field'),
            (r'error_response', 'no error_response field'),
        )),
        'index.html': Rule(alts=('static/index.html', '*/index.html'), baseline=('lessons/*/index.html',),
                           hints=((r'\.data\b', "doesn't read the envelope's .data field"),)),
        'requirements.txt': Rule(need='recommended', alts=('requirements*.txt', 'pyproject.toml')),
        '.env.example': Rule(need='optional'),
        '.gitignore': Rule(need='optional'),
        'tests/conftest.py': Rule(need='optional'),
        'tests/test_api.py': Rule(need='optional', alts=('tests/test_*.py', 'test_*.py'), min_code=6),
        'evidence/pytest_output.txt': Rule(need='optional', alts=('evidence/*.txt',), min_words=20),
        'evidence/http_examples.md': Rule(need='optional', alts=('evidence/*.md',), min_words=80),
        'evidence/': Rule(any_of=('evidence/*', '*.http', 'tests/test_*.py', 'test_*.py')),
    },

    'Performance_Project': {
        '@aliases': {'api': ('measurement_api', 'starter_code')},
        'README.md': Rule(min_words=30, hints=((r'(?i)findings', 'no link to your FINDINGS files'),)),
        '.gitignore': Rule(need='optional'),

        'sqlite/FINDINGS_sqlite.md': Rule(baseline=(FINDINGS_TEMPLATE,), min_words=300,
                                          leftovers=('(paste here)',)),
        'sqlite/01_why.md': Rule(alts=('sqlite/*01*.md', 'sqlite/why.md'), min_words=40,
                                 fallback=('sqlite/FINDINGS_sqlite.md', section(1, 'why it exists'))),
        'sqlite/02_install.md': Rule(alts=('sqlite/*02*.md', 'sqlite/install.md'), min_words=10,
                                     fallback=('sqlite/FINDINGS_sqlite.md', section(2, 'install'))),
        'sqlite/03_connect.md': Rule(alts=('sqlite/*03*.md', 'sqlite/connect.md'), min_words=15,
                                     fallback=('sqlite/FINDINGS_sqlite.md', section(3, 'connect'))),
        'sqlite/04_model.md': Rule(alts=('sqlite/*04*.md', 'sqlite/model.md'), min_words=120,
                                   fallback=('sqlite/FINDINGS_sqlite.md', section(4, 'model'))),
        'sqlite/05_load.md': Rule(alts=('sqlite/*05*.md', 'sqlite/load.md'), min_words=15,
                                  fallback=('sqlite/FINDINGS_sqlite.md', section(5, 'load it'))),
        'sqlite/06_queries.md': Rule(alts=('sqlite/*06*.md', 'sqlite/queries.md'), min_words=15,
                                     fallback=('sqlite/FINDINGS_sqlite.md', section(6, 'quer'))),
        'sqlite/your_turn_checks.sql': Rule(
            baseline=('assignments/performance_project/engines/01_sqlite/04_model/your_turn_checks.sql',),
            blanks=r'(?im)^\s*--\s*(your prediction|what it returned|what it means for the design)\s*:\s*$'),
        'sqlite/my_schema.sql': Rule(min_code=3, hints=(
            (r'(?i)create\s+table', 'no CREATE TABLE'),
            (r'(?i)references|foreign\s+key', 'no foreign keys'),
        )),
        'sqlite/my_load.sql': Rule(
            alts=('sqlite/my_loader.sql', 'sqlite/*load*.sql', 'sqlite/my_load.py', 'sqlite/*load*.py'),
            baseline=('assignments/performance_project/engines/01_sqlite/05_load/load_classroom.sql',),
            min_code=2, hints=((r'(?i)insert', 'no INSERT'),)),

        'duckdb/FINDINGS_duckdb.md': Rule(baseline=(FINDINGS_TEMPLATE,), min_words=300,
                                          leftovers=('(paste here)',), hints=((r'(?i)both', 'no "both" scenario'),)),
        'duckdb/01_why.md': Rule(alts=('duckdb/*01*.md', 'duckdb/why.md'), min_words=60,
                                 fallback=('duckdb/FINDINGS_duckdb.md', section(1, 'why it exists'))),
        'duckdb/03_connect.md': Rule(alts=('duckdb/*03*.md', 'duckdb/connect.md'), min_words=20,
                                     fallback=('duckdb/FINDINGS_duckdb.md', section(3, 'connect'))),
        'duckdb/04_model.md': Rule(alts=('duckdb/*04*.md', 'duckdb/model.md'), min_words=80,
                                   fallback=('duckdb/FINDINGS_duckdb.md', section(4, 'model'))),
        'duckdb/05_load.md': Rule(alts=('duckdb/*05*.md', 'duckdb/load.md'), min_words=60,
                                  fallback=('duckdb/FINDINGS_duckdb.md', section(5, 'load it'))),
        'duckdb/06_queries.md': Rule(alts=('duckdb/*06*.md', 'duckdb/queries.md'), min_words=60,
                                     fallback=('duckdb/FINDINGS_duckdb.md', section(6, 'quer'))),

        'api/pyproject.toml': Rule(copied=True),
        'api/.env.example': Rule(need='optional'),
        'api/driver.py': Rule(copied=True, min_code=10),
        'api/app/__init__.py': Rule(copied=True, min_code=0),
        'api/app/main.py': Rule(baseline=(f'{STARTER}/app/main.py',), min_code=20, todo=True),
        'api/app/experiment.py': Rule(copied=True, min_code=10),
        'api/app/experiment_duckdb.py': Rule(copied=True, min_code=10),
        'api/app/models.py': Rule(copied=True, min_code=1),
        'api/tests/conftest.py': Rule(copied=True),
        'api/tests/test_smoke.py': Rule(copied=True),
        'api/tests/test_your_routes.py': Rule(copied=True),
        'api/results_sqlite/results.csv': Rule(
            alts=('api/results/results.csv',),
            csv_distinct=('db', 6, 'only {n} of 6 databases: run the driver without --sizes for the full run')),
        'api/results_sqlite/results.md': Rule(alts=('api/results/results.md',), min_words=20, generated=True),
        'api/results_duckdb/results.csv': Rule(
            csv_distinct=('db', 6, 'only {n} of 6 databases: run the driver without --sizes for the full run')),
        'api/results_duckdb/results.md': Rule(min_words=20, generated=True),
    },

    'Web_Api_Project': {
        'README.md': Rule(min_words=500, hints=(
            (r'\bA[1-8]\b', 'no checklist for activities A1-A8'),
            (r'(?i)lighthouse', 'no Lighthouse accessibility score'),
            (r'(?i)keyboard', 'no keyboard-only walkthrough result'),
            (r'(?i)checkpoint', 'no checkpoint answers'),
            (r'(?i)screenshots?/|!\[[^\]]*\]\([^)]+\)', 'no screenshots embedded or linked'),
        )),
        'api.py': Rule(alts=('main.py', 'app/main.py', 'app/api.py'), baseline=('lessons/*/api.py',),
                       min_code=40, hints=(
            (r'\bwhole\b', 'no whole-word search parameter (A4)'),
            (r'name_desc', 'no name_desc sort (A6)'),
            (r'X-Cache-Key', 'no X-Cache-Key header (A8)'),
            (r'@app\.patch', 'no PATCH route for changing a price'),
            (r'find_one_and_update', 'no atomic counter for new ids'),
            (r'\bDecimal\b', 'Decimal is never used: how is money handled?'),
            (r're\.escape', 'search text is never passed through re.escape'),
        )),
        'index.html': Rule(alts=('static/index.html', 'templates/index.html', 'public/index.html', '*/index.html'),
                           baseline=('lessons/*/index.html',), must_change=True, hints=(
            (r'(?i)<html[^>]*\blang=', '<html> has no lang attribute'),
            (r'(?i)<label', 'no <label> elements'),
            (r'aria-live|role="(alert|status)"', 'no aria-live region: status messages are not announced'),
            (r'whole', 'no whole-word checkbox (A4)'),
            (r'name_desc', 'no Z-A sort option (A6)'),
            (r'X-Cache-Key', "the page doesn't show X-Cache-Key (A8)"),
        )),
        'requirements.txt': Rule(alts=('requirements*.txt', 'pyproject.toml'), hints=(
            (r'(?im)^\s*"?fastapi', 'fastapi is not listed'),
            (r'(?im)^\s*"?pymongo', 'pymongo is not listed'),
            (r'(?im)^\s*"?redis', 'redis is not listed'),
        )),
        '.env.example': Rule(need='recommended', hints=((r'MONGO_DB', 'MONGO_DB is not listed'),)),
        '.gitignore': Rule(need='optional'),
        'screenshots/': Rule(alts=('images/', 'docs/screenshots/', 'docs/'), folder_has=IMAGES),
    },
}


# ================================================================ output

# Emoji crash older Windows consoles that aren't using UTF-8
try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except (AttributeError, ValueError):
    pass

USE_COLOR = sys.stdout.isatty() and 'NO_COLOR' not in os.environ
if USE_COLOR and os.name == 'nt':
    os.system('')  # turns on ANSI color codes in the Windows console


def color(text, code):
    return f'\033[{code}m{text}\033[0m' if USE_COLOR else text


COLORS = {OK: '32', WARN: '33', BAD: '31', SKIP: '2'}


def bold(text):
    return color(text, '1')


# ================================================================ finding files

def key(name):
    """Folder names compare without case, and with - or space the same as _."""
    return re.sub(r'[\s-]+', '_', name.lower())


def matches(name, patterns):
    return any(fnmatch.fnmatchcase(name.lower(), p.lower()) for p in patterns)


def ci_glob(base, pattern):
    """Paths under `base` matching `pattern`, ignoring capitalization at every level."""
    paths = [base]
    for part in pattern.strip('/').split('/'):
        paths = [c for p in paths if p.is_dir()
                 for c in sorted(p.iterdir()) if fnmatch.fnmatchcase(c.name.lower(), part.lower())]
    return paths


class Folder:
    """Your assignment folder, indexed by lowercase relative path."""

    def __init__(self, path, aliases):
        self.path = path
        self.aliases = aliases
        self.files, self.dirs, self.used = {}, {}, set()
        for dirpath, dirnames, filenames in os.walk(path):
            dirnames[:] = [d for d in dirnames if not matches(d, SKIP_DIRS)]
            here = Path(dirpath)
            rel = here.relative_to(path)
            for d in dirnames:
                self.dirs[(rel / d).as_posix().lower()] = here / d
            for f in filenames:
                if f != '.DS_Store':
                    self.files[(rel / f).as_posix().lower()] = here / f

    def expand(self, patterns):
        """Each pattern, plus the same pattern under every alias of its first folder."""
        for pattern in patterns:
            yield pattern
            first, _, rest = pattern.partition('/')
            for alias in self.aliases.get(first.lower(), ()):
                yield f'{alias}/{rest}'

    def find_all(self, patterns, dirs=False):
        table = self.dirs if dirs else self.files
        found = []
        for pattern in self.expand(patterns):
            p = pattern.strip('/').lower()
            hits = sorted(k for k in table if fnmatch.fnmatchcase(k, p)) if any(c in p for c in '*?[') \
                else [p] if p in table else []
            found += [table[h] for h in hits if table[h] not in found]
        return found

    def find(self, patterns, dirs=False):
        """The first match, preferring a file no other row has claimed."""
        found = self.find_all(patterns, dirs)
        fresh = [p for p in found if p not in self.used]
        return (fresh or found or [None])[0]

    def rel(self, path):
        return path.relative_to(self.path).as_posix()


# ================================================================ judging content

WORD = re.compile(r"[a-z0-9]+(?:'[a-z]+)?")
SQL_WORD = re.compile(r'(?i)\b(create|insert|select|update|delete|with|drop|alter|pragma|attach|'
                      r'replace|begin|commit|copy|install|load)\b')
HEADING = re.compile(r'^(#{1,6})\s+\S')


def read(path):
    try:
        return path.read_text(encoding='utf-8')
    except (UnicodeDecodeError, OSError):
        return None


def words(text):
    return Counter(WORD.findall(text.lower()))


def own_words(text, baselines):
    """Words in `text` beyond what the templates already said."""
    base = Counter()
    for t in baselines:
        base |= words(t)
    return sum((words(text) - base).values())


def outside_fences(text):
    """The lines of a Markdown file that aren't inside ``` code blocks."""
    inside = False
    for line in text.splitlines():
        if line.lstrip().startswith(('```', '~~~')):
            inside = not inside
            continue
        if not inside:
            yield line


def has_markdown(text):
    if re.search(r'(?m)^\s*(```|~~~)', text):
        return True
    patterns = (r'^#{1,6}\s+\S', r'^\s*([-*+]|\d+\.)\s+\S', r'^\s*\|.*\|\s*$', r'^>\s',
                r'\[[^\]]+\]\([^)]+\)', r'\*\*[^*]+\*\*', r'`[^`]+`')
    return any(re.search(p, line) for line in outside_fences(text) for p in patterns)


def md_section(text, heading_regex):
    """The part of a Markdown file under the first heading matching `heading_regex`."""
    lines = list(outside_fences(text))
    for i, line in enumerate(lines):
        m = HEADING.match(line)
        if m and re.search(heading_regex, line, re.I):
            out = [line]
            for later in lines[i + 1:]:
                m2 = HEADING.match(later)
                if m2 and len(m2.group(1)) <= len(m.group(1)):
                    break
                out.append(later)
            return '\n'.join(out)
    return None


def strip_html_comments(text):
    return re.sub(r'<!--.*?-->', '', text, flags=re.S)


def check_markdown(text, baselines, rule):
    body = strip_html_comments(text)
    if not body.strip():
        return BAD, 'empty file'
    n = own_words(body, baselines)
    want = rule.min_words if rule.min_words is not None else 25
    if n == 0:
        return BAD, 'still the placeholder: run the program that writes it' if rule.generated \
            else 'no writing of your own yet (still the template)'
    if n < want:
        return BAD, f'only {n} words of your own (expected about {want}+)'
    if not has_markdown(body):
        return WARN, f'{n} words, but no Markdown formatting: add headings, lists, or tables'
    return OK, f'{n} words' if rule.generated else f'{n} words of your own'


def check_plain_text(text, baselines, rule):
    n = own_words(text, baselines)
    want = rule.min_words if rule.min_words is not None else 10
    if n == 0:
        return BAD, 'nothing of your own yet (still the template)'
    if n < want:
        return BAD, f'only {n} words of your own (expected about {want}+)'
    return OK, f'{n} words of your own'


def count_statements(tree):
    """Real statements: not imports, pass, docstrings, or a bare `...`."""
    n = 0
    for node in ast.walk(tree):
        if not isinstance(node, ast.stmt) or isinstance(node, (ast.Import, ast.ImportFrom, ast.Pass)):
            continue
        if isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant):
            continue
        n += 1
    return n


def check_python(text, baselines, rule, baseline_names):
    try:
        tree = ast.parse(text)
    except SyntaxError as e:
        code = [ln for ln in text.splitlines() if ln.strip() and not ln.strip().startswith('#')]
        if not code:
            return BAD, 'no Python code yet (only comments)'
        return WARN, f"syntax error on line {e.lineno} ({e.msg}): the code is there, but it won't run"
    n = count_statements(tree)
    want = rule.min_code if rule.min_code is not None else 2
    if n == 0 and want > 0:
        return BAD, 'no Python code yet (only comments)'
    if n < want:
        return BAD, f'only {n} statement(s) of code (expected about {want}+)'
    if not rule.copied:
        dump = ast.dump(tree)
        for name, base in zip(baseline_names, baselines):
            try:
                if ast.dump(ast.parse(base)) == dump:
                    return BAD, f'unchanged from {name}: this file needs your changes'
            except SyntaxError:
                pass
    if rule.copied:
        return OK, 'copied starter file' + (f', {n} statements' if n else '')
    return OK, f'{n} statements of code'


def strip_sql_comments(text):
    return re.sub(r'--[^\n]*', '', re.sub(r'/\*.*?\*/', '', text, flags=re.S))


def check_sql(text, baselines, rule, baseline_names):
    code = strip_sql_comments(text)
    n = sum(1 for s in code.split(';') if SQL_WORD.search(s))
    want = rule.min_code if rule.min_code is not None else 1
    if n == 0:
        return BAD, 'no SQL yet (only comments)'
    if n < want:
        return BAD, f'only {n} SQL statement(s) (expected about {want}+)'
    if not rule.blanks:  # where you fill in prompts, the queries are SUPPOSED to match
        squash = lambda s: ' '.join(s.lower().split())
        for name, base in zip(baseline_names, baselines):
            if squash(strip_sql_comments(base)) == squash(code):
                return BAD, f'unchanged from {name}: adapt it to your own schema'
    return OK, f'{n} SQL statements'


def check_csv(text, rule):
    rows = [r for r in csv.reader(io.StringIO(text)) if any(c.strip() for c in r)]
    if not rows:
        return BAD, 'empty file'
    if len(rows) == 1:
        return BAD, 'header only: no data rows yet (run the program that writes it)'
    note = f'{len(rows) - 1} data rows'
    if rule.csv_distinct:
        column, want, message = rule.csv_distinct
        header = [h.strip().lower() for h in rows[0]]
        if column in header:
            i = header.index(column)
            n = len({r[i] for r in rows[1:] if len(r) > i})
            if n < want:
                return WARN, f'{note}, but {message.format(n=n)}'
    return OK, note


def check_html(text, baselines, baseline_names, rule):
    tags = re.findall(r'<[a-zA-Z][^>]*>', strip_html_comments(text))
    if not tags:
        return BAD, 'no HTML yet (only a comment)'
    squash = lambda s: ' '.join(s.split())
    for name, base in zip(baseline_names, baselines):
        if squash(base) == squash(text):
            if rule.must_change:
                return BAD, f'unchanged from {name}: this page needs your changes'
            return WARN, f'unchanged from {name}: does the page still work with the new response shape?'
    return OK, f'{len(tags)} HTML tags'


def check_toml(text):
    if tomllib is None:
        return OK, 'found (needs Python 3.11+ to look inside)'
    try:
        data = tomllib.loads(text)
    except tomllib.TOMLDecodeError as e:
        return WARN, f'not valid TOML: {e}'
    return (OK, f'{len(data)} section(s)') if data else (BAD, 'no settings yet (only comments)')


def check_notebook(text):
    try:
        cells = json.loads(text).get('cells', [])
    except (json.JSONDecodeError, AttributeError):
        return WARN, 'not a valid notebook file'
    code = [c for c in cells if c.get('cell_type') == 'code' and ''.join(c.get('source', [])).strip()]
    return (OK, f'{len(code)} code cells') if code else (BAD, 'no code cells with code in them')


def check_lines(text, rule, what='lines'):
    """Shell scripts, JS, .gitignore, .env.example...: lines that aren't comments."""
    lines = [ln for ln in text.splitlines() if ln.strip() and not ln.strip().startswith(('#', '//'))]
    if not lines:
        return BAD, 'only comments so far'
    return OK, f'{len(lines)} {what if len(lines) != 1 else what.rstrip("s")}'


def check_content(path, rule, reference):
    """(status, note) for one found file."""
    suffix = path.suffix.lower()
    if matches(path.name, IMAGES):
        size = path.stat().st_size
        return (OK, f'{max(1, size // 1024)} KB') if size else (BAD, 'empty file')

    text = read(path)
    if text is None:
        return (OK, 'found') if path.stat().st_size else (BAD, 'empty file')
    if not text.strip():
        if rule.min_code == 0:
            return OK, 'found (empty is fine here)'
        return BAD, 'empty file'

    # The files you started from: their text doesn't count as yours
    names, code_baselines = [], []
    for pattern in rule.baseline:
        for p in ci_glob(ROOT, pattern):
            names.append(p.relative_to(ROOT).as_posix())
            code_baselines.append(read(p) or '')
    placeholder = [read(reference) or ''] if reference and reference.is_file() else []
    baselines = placeholder + code_baselines

    if suffix in ('.md', '.markdown'):
        status, note = check_markdown(text, baselines, rule)
    elif suffix == '.py':
        status, note = check_python(text, code_baselines, rule, names)
    elif suffix == '.sql':
        status, note = check_sql(text, code_baselines, rule, names)
    elif suffix == '.csv':
        status, note = check_csv(text, rule)
    elif suffix in ('.html', '.htm'):
        status, note = check_html(text, code_baselines, names, rule)
    elif suffix == '.toml':
        status, note = check_toml(text)
    elif suffix == '.ipynb':
        status, note = check_notebook(text)
    elif suffix == '.json':
        try:
            status, note = (OK, 'valid JSON') if json.loads(text) else (BAD, 'empty JSON')
        except json.JSONDecodeError as e:
            status, note = WARN, f'not valid JSON: {e.msg} on line {e.lineno}'
    elif path.name.lower().startswith('requirements') and suffix == '.txt':
        status, note = check_lines(text, rule, 'packages')
    elif suffix in ('.txt', '.log', '.out', '.http'):
        status, note = check_plain_text(text, baselines, rule)
    else:
        status, note = check_lines(text, rule)

    if status == BAD:
        return status, note
    extra = []
    if rule.blanks:
        total = len(re.findall(rule.blanks, ''.join(baselines)))
        left = len(re.findall(rule.blanks, text))
        if total and left == total:
            return BAD, f'none of the {total} prompts filled in yet'
        if left:
            extra.append(f'{left} of {total} prompts still blank')
        elif total:
            note = f'all {total} prompts filled in'
    for leftover in rule.leftovers:
        if leftover.lower() in text.lower():
            extra.append(f'still contains "{leftover}"')
    if rule.todo:
        n = len(re.findall(r'(?m)#\s*TODO\b', text))
        if n:
            extra.append(f'{n} TODO marker(s) left: delete each one once its route works')
    extra += [message for regex, message in rule.hints if not re.search(regex, text)]
    if extra:
        return WARN, note + '; ' + '; '.join(extra)
    return status, note


# ================================================================ one assignment

def missing(rule, note='missing'):
    if rule.need == 'optional':
        return SKIP, 'optional, not there'
    if rule.need == 'recommended':
        return WARN, f'{note} (recommended)'
    return BAD, note


def soften(status, rule):
    """Problems in optional or recommended files are warnings, not failures."""
    return WARN if status == BAD and rule.need != 'required' else status


def with_content(folder, files, ref_root):
    """The files that hold something of your own (judged against their template, if any)."""
    good = []
    for p in files:
        status, _ = check_content(p, Rule(need='optional'), ref_root / folder.rel(p))
        if status != BAD:
            good.append(p)
    return good


def check_entry(folder, entry, rule, ref_root):
    """(status, note) for one row of the table."""
    patterns = (entry,) + rule.alts

    if rule.folder_has:
        found = folder.find(patterns, dirs=True)
        if found is None:
            return missing(rule)
        files = [p for p in found.rglob('*') if p.is_file() and matches(p.name, rule.folder_has)]
        folder.used.update(files)
        filled = with_content(folder, files, ref_root)
        where = '' if key(found.name) == key(entry.strip('/')) else f'found as "{folder.rel(found)}/", '
        if not files:
            return soften(BAD, rule), where + 'no ' + ', '.join(rule.folder_has[:3]) + ' files in it yet'
        if not filled:
            return soften(BAD, rule), where + f'{len(files)} file(s), but none with data or writing yet'
        return OK, where + f'{len(filled)} file(s) with content'

    if rule.any_of:
        found = folder.find_all(rule.any_of)
        filled = with_content(folder, found, ref_root)
        if not filled:
            return missing(rule, 'files are there, but still the template' if found else 'missing')
        more = f' and {len(filled) - 1} more' if len(filled) > 1 else ''
        return OK, f'{folder.rel(filled[0])}{more}'

    # Each completed/<assignment>/README.md explains the example; it isn't a template you copy
    reference = None if entry.lower() == 'readme.md' else ref_root / entry
    found = folder.find(patterns)
    if found is None and rule.fallback:
        host_name, regex = rule.fallback
        host = folder.find((host_name,))
        text = read(host) if host else None
        if text and re.search(regex, text, re.I | re.M):
            if host.suffix.lower() == '.md':
                part = md_section(text, regex)
                if part:
                    status, note = check_markdown(part, [], rule)
                    return soften(status, rule), f'as a section of {folder.rel(host)}: {note}'
            else:
                return OK, f'found inside {folder.rel(host)}'
    if found is None:
        return missing(rule)

    folder.used.add(found)
    example = ref_root / entry
    if reference is None and example.is_file():  # a README: make sure it isn't the example itself
        text = read(found) or ''
        total = sum(words(text).values())
        if total and own_words(text, [read(example) or '']) < 0.1 * total:
            return soften(BAD, rule), "this is the example README from completed/, not your own"
    status, note = check_content(found, rule, reference)
    if folder.rel(found).lower() != entry.lower():
        note = f'found as "{folder.rel(found)}": {note}'
    return soften(status, rule), note


def git(folder, *args):
    try:
        out = subprocess.run(['git', '-C', str(folder), *args], capture_output=True, text=True)
    except (FileNotFoundError, OSError):
        return None
    return out.stdout if out.returncode == 0 else None


def junk_of(rel):
    """The folder or file in `rel` that shouldn't be committed, or None."""
    parts = rel.split('/')
    for i, part in enumerate(parts[:-1]):
        if matches(part, JUNK_DIRS):
            return '/'.join(parts[:i + 1]) + '/'
    return rel if matches(parts[-1], JUNK_FILES) else None


def junk_rows(path):
    """Rows for databases, virtual environments, and secrets that git would pick up."""
    rows = []
    if git(path, 'rev-parse', '--is-inside-work-tree') is not None:
        tracked = {j for f in git(path, 'ls-files', '-z').split('\0') if f and (j := junk_of(f))}
        loose = {j for f in git(path, 'ls-files', '-z', '--others', '--exclude-standard').split('\0')
                 if f and (j := junk_of(f))} - tracked
        rows += [(BAD, j, f'committed: run  git rm -r --cached "{j}"  and add it to .gitignore')
                 for j in sorted(tracked)]
        rows += [(WARN, j, 'not ignored: add it to .gitignore before you commit') for j in sorted(loose)]
    else:
        found = set()
        for dirpath, dirnames, filenames in os.walk(path):
            rel = Path(dirpath).relative_to(path)
            for d in [d for d in dirnames if matches(d, JUNK_DIRS)]:
                found.add((rel / d).as_posix() + '/')
                dirnames.remove(d)
            found.update((rel / f).as_posix() for f in filenames if matches(f, JUNK_FILES))
        rows += [(WARN, j, 'not in a git repo: make sure .gitignore keeps this out')
                 for j in sorted(found)]
    return rows or [(OK, '(databases, .venv, .env, ...)', "nothing here that shouldn't be committed")]


def entries(name):
    """The rows for one assignment: every file in completed/<name>, plus folder and group rules."""
    rules = {k: v for k, v in SPEC.get(name, {}).items() if not k.startswith('@')}
    ref = COMPLETED / name
    names = {p.relative_to(ref).as_posix() for p in ref.rglob('*')
             if p.is_file() and p.name not in ('.gitkeep', '.DS_Store')}
    names |= set(rules)
    # files at the top first, then each folder (its own row before its files)
    order = lambda e: ('/' in e, e.lower())
    return [(e, rules.get(e, Rule())) for e in sorted(names, key=order)]


def check_assignment(name, path):
    """Print the table for one assignment folder. Return (failures, warnings)."""
    folder = Folder(path, SPEC.get(name, {}).get('@aliases', {}))
    rows = []
    for e, rule in entries(name):
        status, note = check_entry(folder, e, rule, COMPLETED / name)
        rows.append((status, e, note))

    for nested in (name, 'your_repo', 'your-repo'):
        inner = folder.dirs.get(key(nested)) or folder.dirs.get(nested.lower())
        if inner:
            rows.append((WARN, folder.rel(inner) + '/', 'nested folder: move its contents up one level'))

    junk = junk_rows(path)
    width = max(len('File'), *(len(item) for _, item, _ in rows + junk))

    def show(status, item, note):
        print(f'   {status}  {item:<{width}}  {color(note, COLORS[status])}')

    print()
    same = '' if path.name == name else f'   (compared with completed/{name})'
    print(bold(f'📂 {path.parent.name}/{path.name}') + same)
    print(f'   {"":2}  {"File":<{width}}  Result')
    print(f'   {"":2}  {"-" * width}  {"-" * 40}')
    for row in rows:
        show(*row)
    print(f'   {"":2}  {bold("Keep out of git")}')
    for row in junk:
        show(*row)

    extras = [p for p in folder.files.values()
              if p not in folder.used and p.name != '.gitkeep' and junk_of(folder.rel(p)) is None]
    if extras:
        print(f'   ℹ️   {len(extras)} other file(s) not in the example: that\'s fine')

    every = rows + junk
    bad = sum(s == BAD for s, _, _ in every)
    warn = sum(s == WARN for s, _, _ in every)
    good = sum(s == OK for s, _, _ in every)
    summary = f'{good} ok, {warn} to look at, {bad} missing or unfinished'
    print('   ' + color(summary, COLORS[BAD if bad else WARN if warn else OK]))
    return bad, warn


# ================================================================ main

def assignment_names():
    return sorted(p.name for p in COMPLETED.iterdir() if p.is_dir() and not p.name.startswith('.'))


def resolve(arg, known):
    """'caching', 'Caching_Project', or 'Caching_Project/' -> 'Caching_Project'."""
    k = key(Path(arg.rstrip('/\\')).name)
    exact = [n for n in known if key(n) == k]
    hits = exact or [n for n in known if key(n).startswith(k)]
    if len(hits) == 1:
        return hits[0]
    hint = f'matches {", ".join(hits)}' if hits else 'matches no assignment'
    sys.exit(f'{BAD} "{arg}" {hint}. Choose from:\n   ' + '\n   '.join(known))


def find_repo(known):
    """Your repo, and the one assignment to check if you're standing inside it."""
    cwd = Path.cwd().resolve()
    for p in [cwd, *cwd.parents]:
        for n in known:
            if key(p.name) == key(n):
                return p.parent, [n]
    top = git(cwd, 'rev-parse', '--show-toplevel')
    return (Path(top.strip()).resolve() if top else cwd), []


def main(argv=None):
    parser = argparse.ArgumentParser(
        description='Check your assignment folders against the examples in completed/.',
        epilog='Run with no arguments from your course repo to check every assignment folder in it.')
    parser.add_argument('assignments', nargs='*', help='which assignments (a unique prefix is enough)')
    parser.add_argument('--repo', type=Path, help='your course repo (default: the repo you are in)')
    args = parser.parse_args(argv)

    if not COMPLETED.is_dir():
        sys.exit(f'{BAD} Folder not found: {COMPLETED}')
    known = assignment_names()

    if args.repo:
        repo, here = args.repo.expanduser().resolve(), []
    else:
        repo, here = find_repo(known)
    if not repo.is_dir():
        sys.exit(f'{BAD} Not a folder: {repo}')
    if (repo == ROOT or ROOT in repo.parents) and repo != COMPLETED:
        sys.exit(f'{BAD} {repo} is inside the field guide, not your course repo.\n'
                 f'   Run this from your own repo, or pass --repo, e.g.\n'
                 f'   python {Path(__file__).name} --repo ~/5303/my-repo')

    wanted = list(dict.fromkeys(resolve(a, known) for a in args.assignments)) or here or known
    present = {key(p.name): p for p in repo.iterdir() if p.is_dir()}

    results, not_started = [], []
    for name in wanted:
        path = present.get(key(name))
        if path is None:
            not_started.append(name)
        else:
            results.append(check_assignment(name, path))

    print()
    if not results:
        print(f'{BAD} No assignment folders found in {repo}')
        print(f'   Expected one or more of: {", ".join(known)}')
        print('   (run this from your course repo, or pass --repo)')
        return 1
    if not_started:
        print(f'{SKIP} Not started yet (no folder in {repo.name}/): {", ".join(not_started)}')

    done = sum(bad == 0 for bad, _ in results)
    warnings = sum(w for _, w in results)
    line = f'{OK if done == len(results) else BAD} {done} of {len(results)} assignment folder(s) ' \
           f'have everything required'
    if warnings:
        line += f' ({warnings} warning{"s" * (warnings != 1)} to look at)'
    print(bold(color(line, COLORS[OK if done == len(results) else BAD])))
    print(color(f'   {OK} ok   {WARN} worth a look   {BAD} missing or still the template   '
                f'{SKIP} optional', COLORS[SKIP]))
    print(color('   This checks that your work is there, not that it is correct.', COLORS[SKIP]))
    return 0 if done == len(results) else 1


if __name__ == '__main__':
    sys.exit(main())
