import os, zipfile, subprocess, tempfile, re, json, textwrap
from pathlib import Path

zip_path = Path(r'C:\Users\perso\OneDrive\Documents\esgi\yearly_project_5\jadus\modules.zip')
if not zip_path.exists():
    raise SystemExit(f'missing zip {zip_path}')

with zipfile.ZipFile(zip_path) as archive:
    files = sorted([n for n in archive.namelist() if n.lower().endswith('.ps1') and 'temp/' not in n.lower()])

    for name in files:
        content = archive.read(name).decode('utf-8', errors='replace')
        # try to extract function name
        m = re.search(r'(?m)^\s*function\s+([A-Za-z0-9_-]+)\s*(?:\{|\()', content)
        func = m.group(1) if m else os.path.basename(name).rsplit('.',1)[0]
        # create temp ps1 and execute it
        with tempfile.NamedTemporaryFile('w', suffix='.ps1', delete=False, encoding='utf-8') as f:
            f.write(content)
            tmp = f.name
        try:
            proc = subprocess.run(
                ['powershell', '-NoLogo', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', tmp],
                capture_output=True,
                text=True,
                timeout=60,
            )
            status = 'OK' if proc.returncode == 0 else 'FAIL'
            stdout = (proc.stdout or '').strip().splitlines()[:6]
            stderr = (proc.stderr or '').strip().splitlines()[:6]
            print(json.dumps({'name': name, 'function': func, 'status': status, 'rc': proc.returncode, 'stdout': stdout, 'stderr': stderr}, ensure_ascii=False))
        except Exception as e:
            print(json.dumps({'name': name, 'function': func, 'status': 'ERROR', 'error': str(e)}, ensure_ascii=False))
        finally:
            try: os.unlink(tmp)
            except Exception: pass

