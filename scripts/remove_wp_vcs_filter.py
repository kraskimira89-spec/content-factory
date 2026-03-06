"""Удаляет ошибочный add_filter из wp-config.php на VPS."""
import base64
import os
import subprocess
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / "config" / ".env")
host = os.getenv("VPS_HOST", "").strip() or "91.229.11.147"
user = os.getenv("VPS_USER", "root").strip()
wp_config = "/root/sites/entuziastov75VPS/www/entuziastov75.ru/wp-config.php"

script = f'''
path = "{wp_config}"
with open(path) as f:
    lines = f.readlines()
new_lines = []
skip = 0
i = 0
while i < len(lines):
    line = lines[i]
    if "automatic_updates_is_vcs_checkout" in line or "Разрешить фоновые обновления при наличии .git" in line:
        i += 1
        if i < len(lines) and lines[i].strip() == "":
            i += 1
        continue
    new_lines.append(line)
    i += 1
with open(path, "w") as f:
    f.writelines(new_lines)
print("Removed")
'''
b64 = base64.b64encode(script.encode()).decode()
cmd = f"echo {b64} | base64 -d | python3"
result = subprocess.run(
    ["ssh", "-o", "StrictHostKeyChecking=no", f"{user}@{host}", cmd],
    capture_output=True,
    text=True,
    timeout=30,
)
print(result.stdout or result.stderr)
exit(result.returncode)
