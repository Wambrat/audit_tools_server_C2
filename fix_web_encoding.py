from pathlib import Path

root = Path(__file__).resolve().parent
web_dir = root / "web"
text_exts = {".html", ".js", ".css", ".md", ".txt", ".json"}
suspect = (
    "Ã", "Â", "â€™", "â€", "â€“", "Ã©", "Ã¨", "Ã§", "Ã¼", "Ã±", "Ã¢", "Ã¯",
    "Ã‰", "Ã ", "Ã¹", "Ã´", "Ã®", "Ãª", "â€œ", "â€", "â€˜", "â€”", "â€•"
)

fixed_files = []
for path in sorted(web_dir.rglob("*")):
    if not path.is_file() or path.suffix.lower() not in text_exts:
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

    if not any(marker in text for marker in suspect):
        continue

    try:
        corrected = text.encode("latin-1").decode("utf-8")
    except Exception:
        continue

    if corrected == text:
        continue

    path.write_text(corrected, encoding="utf-8", newline="")
    fixed_files.append(str(path.relative_to(root)))

print(f"FIXED={len(fixed_files)}")
for item in fixed_files:
    print(item)
