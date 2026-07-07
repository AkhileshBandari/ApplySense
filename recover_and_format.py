import os, sys, ast, json, pathlib

# Extensions to check
EXTENSIONS = {
    '.json', '.js', '.jsx', '.ts', '.tsx', '.mjs', '.cjs', '.py', '.java', '.kt', '.go',
    '.html', '.css', '.scss', '.sass', '.yaml', '.yml', '.env', '.md', '.Dockerfile',
    '.dockerfile', '.txt', '.sql', '.sh', '.ps1'
}

def is_corrupted(content: str) -> bool:
    stripped = content.strip()
    if len(stripped) < 2:
        return False
    # starts and ends with matching quote (single or double)
    if (stripped[0] == stripped[-1] == '"') or (stripped[0] == stripped[-1] == "'"):
        # look for escaped newline/tab or escaped quotes inside
        if '\\n' in stripped or '\\t' in stripped or '\\"' in stripped or "\\'" in stripped:
            return True
    return False

def repair_content(path: pathlib.Path, content: str) -> str:
    # unescape using ast.literal_eval which interprets escape sequences
    try:
        unescaped = ast.literal_eval(content.strip())
    except Exception as e:
        # fallback: replace manually
        unescaped = content.strip()[1:-1]
        unescaped = unescaped.replace('\\n', '\n').replace('\\t', '\t').replace('\\"', '"').replace("\\'", "'")
    # format JSON if needed
    if path.suffix.lower() == '.json':
        try:
            data = json.loads(unescaped)
            return json.dumps(data, indent=2, ensure_ascii=False)
        except Exception:
            # not valid JSON, return raw unescaped
            return unescaped
    # For other types, just return unescaped string
    return unescaped

def main(root_dir: str):
    root = pathlib.Path(root_dir)
    repaired = []
    for dirpath, _, filenames in os.walk(root):
        for fname in filenames:
            fpath = pathlib.Path(dirpath) / fname
            if fpath.suffix.lower() not in EXTENSIONS:
                continue
            try:
                with open(fpath, 'r', encoding='utf-8') as f:
                    content = f.read()
            except Exception:
                continue
            if is_corrupted(content):
                new_content = repair_content(fpath, content)
                try:
                    with open(fpath, 'w', encoding='utf-8') as f:
                        f.write(new_content)
                    repaired.append(str(fpath))
                except Exception as e:
                    print(f"Failed to write {fpath}: {e}", file=sys.stderr)
    # summary output
    print('Repaired files:')
    for p in repaired:
        print(p)

if __name__ == '__main__':
    # default to current working directory if not provided
    root_dir = sys.argv[1] if len(sys.argv) > 1 else os.getcwd()
    main(root_dir)
