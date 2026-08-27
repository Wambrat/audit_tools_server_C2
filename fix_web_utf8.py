from pathlib import Path

root = Path(r"C:\Users\perso\OneDrive\Documents\esgi\yearly_project_5\server_C2\web")
exts = {".html", ".js", ".css", ".md", ".txt", ".json", ".yml", ".yaml"}
markers = (
    "Ã", "Â", "â€™", "â€", "â€“", "Ã©", "Ã¨", "Ã§", "Ã¼", "Ã±", "Ã¢", "Ã¯",
    "Ã‰", "Ã ", "Ã¹", "Ã´", "Ã®", "Ãª", "ðŸ", "â†", "â„", "âš"
)
count = 0
for path in sorted(root.rglob("*")):
    if not path.is_file() or path.suffix.lower() not in exts:
        continue
    try:
        raw = path.read_bytes()
    except Exception:
        continue
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        try:
            text = raw.decode("cp1252")
        except Exception:
            continue
    if not any(marker in text for marker in markers):
        continue
    try:
        corrected = text.encode("latin-1").decode("utf-8")
    except UnicodeEncodeError:
        corrected = text.encode("latin-1", "ignore").decode("utf-8", "ignore")
    if corrected == text:
        continue
    path.write_text(corrected, encoding="utf-8", newline="")
    count += 1
    print(f"fixed {path.relative_to(root.parent)}")
print(f"TOTAL_FIXED={count}")
