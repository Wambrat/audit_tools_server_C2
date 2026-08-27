from pathlib import Path

root = Path(__file__).resolve().parent
web_dir = root / 'web'
text_exts = {'.html', '.js', '.css', '.md', '.txt', '.json', '.yml', '.yaml', '.py', '.sh', '.ps1'}
suspect = (
    'Ã', 'Â', 'â€™', 'â€', 'â€“', 'Ã©', 'Ã¨', 'Ã§', 'Ã¼', 'Ã±', 'Ã¢', 'Ã¯',
    'Ã‰', 'Ã ', 'Ã¹', 'Ã´', 'Ã®', 'Ãª', 'â€œ', 'â€', 'â€˜', 'â€”', 'â€•'
)

fixed_web = []
for path in sorted(web_dir.rglob('*')):
    if not path.is_file() or path.suffix.lower() not in text_exts:
        continue
    try:
        raw = path.read_bytes()
    except Exception:
        continue
    try:
        text = raw.decode('utf-8')
    except UnicodeDecodeError:
        try:
            text = raw.decode('cp1252')
        except Exception:
            continue

    if not any(marker in text for marker in suspect):
        continue

    corrected = text.encode('latin-1').decode('utf-8')
    if corrected == text:
        continue

    path.write_text(corrected, encoding='utf-8', newline='')
    fixed_web.append(str(path.relative_to(root)))

idna_path = root / '.venv' / 'Lib' / 'site-packages' / 'idna' / 'idnadata.py'
if idna_path.exists():
    text = idna_path.read_text(encoding='utf-8')
    old = '0x10FC100010Fjadus,'
    new = '0x10FC100010FC1,'
    if old in text:
        text = text.replace(old, new)
        idna_path.write_text(text, encoding='utf-8', newline='')
        print(f'fixed {idna_path.relative_to(root)}')

print(f'FIXED_WEB={len(fixed_web)}')
for item in fixed_web:
    print(item)
