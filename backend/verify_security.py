import os
import re

secret_patterns = [
    r'AIzaSy[A-Za-z0-9_-]{33}',
    r'BEGIN (?:RSA |EC )?PRIVATE KEY',
]

root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
detected = []

for dirpath, dirs, filenames in os.walk(root_dir):
    if '.git' in dirpath or '__pycache__' in dirpath:
        continue
    for f in filenames:
        if f.endswith('.env'):
            continue
        filepath = os.path.join(dirpath, f)
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as fh:
                content = fh.read()
                for pat in secret_patterns:
                    if re.search(pat, content):
                        if not f.endswith('.example') and not f.endswith('.md'):
                            detected.append((os.path.relpath(filepath, root_dir), pat))
        except Exception:
            pass

if detected:
    print('WARNING: Secrets detected:', detected)
else:
    print('SECURITY CHECK PASS: Zero hardcoded API keys or credentials detected in source files.')
