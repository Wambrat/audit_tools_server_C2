import re
import shutil
import zipfile
from pathlib import Path

root = Path(__file__).resolve().parents[1]
zip_path = root / 'modules.zip'
backup_path = root / 'modules.zip.bak'

if not zip_path.exists():
    raise FileNotFoundError(f'Missing archive: {zip_path}')

shutil.copy2(zip_path, backup_path)

pattern = re.compile(r'(?ms)^\s*function\s+([A-Za-z0-9_-]+)\s*(?:\{|\()')
updated = 0

with zipfile.ZipFile(backup_path, 'r') as src, zipfile.ZipFile(zip_path, 'w', compression=zipfile.ZIP_DEFLATED) as dst:
    for info in src.infolist():
        data = src.read(info.filename)

        if info.filename.lower().endswith('.ps1'):
            text = data.decode('utf-8', errors='replace')
            match = pattern.search(text)

            if match:
                func_name = match.group(1)
                call_re = re.compile(rf'(?m)^\s*(?:&\s*)?{re.escape(func_name)}\s*(?:\(|$)')

                if not call_re.search(text):
                    text = text.rstrip()
                    if not text.endswith('\n'):
                        text += '\n'
                    text += f'\n{func_name}\n'
                    updated += 1

            data = text.encode('utf-8', errors='replace')

        dst.writestr(info, data)

print(f'updated_scripts={updated}')
