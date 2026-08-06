import io
import os
import tokenize
from pathlib import Path

ROOT = Path('.').resolve()
CODE_EXTS = {'.py', '.js', '.jsx', '.ts', '.tsx', '.css', '.scss', '.html', '.htm', '.vue'}
SKIP_DIRS = {
    '.git',
    '__pycache__',
    '.venv',
    'venv',
    'node_modules',
    'dist-electron',
    'models',
    'datasets',
    'runs',
    'public',
    'assets',
}


def strip_python(text: str) -> str:
    try:
        tokens = []
        for tok in tokenize.generate_tokens(io.StringIO(text).readline):
            if tok.type == tokenize.COMMENT:
                continue
            tokens.append(tok)
        return tokenize.untokenize(tokens)
    except Exception:
        return text


def strip_js_like(text: str) -> str:
    out = []
    i = 0
    n = len(text)
    in_single = False
    in_double = False
    in_template = False
    in_line_comment = False
    in_block_comment = False
    escape = False

    while i < n:
        ch = text[i]
        nxt = text[i + 1] if i + 1 < n else ''

        if in_line_comment:
            if ch == '\n':
                in_line_comment = False
                out.append(ch)
            i += 1
            continue

        if in_block_comment:
            if ch == '*' and nxt == '/':
                in_block_comment = False
                i += 2
            else:
                if ch == '\n':
                    out.append(ch)
                i += 1
            continue

        if in_single:
            out.append(ch)
            if escape:
                escape = False
            elif ch == '\\':
                escape = True
            elif ch == "'":
                in_single = False
            i += 1
            continue

        if in_double:
            out.append(ch)
            if escape:
                escape = False
            elif ch == '\\':
                escape = True
            elif ch == '"':
                in_double = False
            i += 1
            continue

        if in_template:
            out.append(ch)
            if escape:
                escape = False
            elif ch == '\\':
                escape = True
            elif ch == '`':
                in_template = False
            i += 1
            continue

        if ch == '/' and nxt == '/':
            in_line_comment = True
            i += 2
            continue
        if ch == '/' and nxt == '*':
            in_block_comment = True
            i += 2
            continue
        if ch == "'":
            in_single = True
            out.append(ch)
            i += 1
            continue
        if ch == '"':
            in_double = True
            out.append(ch)
            i += 1
            continue
        if ch == '`':
            in_template = True
            out.append(ch)
            i += 1
            continue

        out.append(ch)
        i += 1

    return ''.join(out)


def strip_html(text: str) -> str:
    out = []
    i = 0
    n = len(text)
    while i < n:
        if text.startswith('<!--', i):
            end = text.find('-->', i + 4)
            if end == -1:
                break
            i = end + 3
            continue
        out.append(text[i])
        i += 1
    return ''.join(out)


def process_file(path: Path) -> bool:
    try:
        text = path.read_text(encoding='utf-8')
    except Exception:
        return False

    ext = path.suffix.lower()
    if ext == '.py':
        new_text = strip_python(text)
    elif ext in {'.html', '.htm', '.vue'}:
        new_text = strip_html(text)
    else:
        new_text = strip_js_like(text)

    if new_text != text:
        path.write_text(new_text, encoding='utf-8')
        return True
    return False


changed = []
for path in ROOT.rglob('*'):
    if not path.is_file():
        continue
    if path.suffix.lower() not in CODE_EXTS:
        continue
    if any(part in SKIP_DIRS for part in path.parts):
        continue
    if process_file(path):
        changed.append(str(path.relative_to(ROOT)))

print(f'CHANGED={len(changed)}')
for rel in changed:
    print(rel)
