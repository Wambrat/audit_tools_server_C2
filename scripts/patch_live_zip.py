import zipfile
import os
from pathlib import Path

root = Path(r'C:\Users\perso\OneDrive\Documents\esgi\yearly_project_5\jadus')
zip_path = root / 'modules.zip'
if not zip_path.exists():
    raise FileNotFoundError(f'Missing archive: {zip_path}')

old = 'if ($results.StandardUserPolicy -isnot $null -and $results.StandardUserPolicy -isnot [array]) {'
new = 'if (($null -ne $results.StandardUserPolicy) -and ($results.StandardUserPolicy -isnot [array])) {'

tmp_path = root / 'modules.zip.tmp'
entries = []
updated = 0

with zipfile.ZipFile(zip_path, 'r') as src:
    for info in src.infolist():
        data = src.read(info.filename)
        if info.filename.lower().endswith('.ps1'):
            text = data.decode('utf-8', errors='replace')
            if old in text:
                text = text.replace(old, new)
                updated += 1
                data = text.encode('utf-8', errors='replace')
        entries.append((info, data))

with zipfile.ZipFile(tmp_path, 'w', compression=zipfile.ZIP_DEFLATED) as dst:
    for info, data in entries:
        dst.writestr(info, data)

if zip_path.exists():
    os.remove(zip_path)
os.replace(tmp_path, zip_path)

print(f'updated_occurrences={updated}')

