"""Добавляет фильтр automatic_updates_is_vcs_checkout в wp-config.php на VPS."""
import base64
import os
import subprocess
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / "config" / ".env")
host = os.getenv("VPS_HOST", "").strip() or "91.229.11.147"
user = os.getenv("VPS_USER", "root").strip()
wp_config = "/root/sites/entuziastov75VPS/www/entuziastov75.ru/wp-config.php"

add_block = "/** Разрешить фоновые обновления при наличии .git (VCS). */\n"
add_block += "add_filter( 'automatic_updates_is_vcs_checkout', '__return_false' );\n\n"
add_block_b64 = base64.b64encode(add_block.encode()).decode()

script = f'''
import base64
path = "{wp_config}"
block = base64.b64decode("{add_block_b64}").decode()
marker = "/* That's all, stop editing! Happy publishing. */"
with open(path) as f:
    c = f.read()
if "automatic_updates_is_vcs_checkout" in c:
    print("Already present")
    exit(0)
c = c.replace(marker, block + marker)
with open(path, "w") as f:
    f.write(c)
print("Added")
'''
b64 = base64.b64encode(script.encode()).decode()
cmd = f"echo {b64} | base64 -d | python3"
result = subprocess.run(
    ["ssh", "-o", "StrictHostKeyChecking=no", f"{user}@{host}", cmd],
    capture_output=True,
    text=True,
    timeout=30,
)
print(result.stdout or "")
if result.stderr:
    print("STDERR:", result.stderr)
exit(result.returncode)
