"""Отключает WP_DEBUG и WP_DEBUG_LOG в wp-config.php (продакшен)."""
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
    c = f.read()
# WP_DEBUG true -> false
c = c.replace("define( 'WP_DEBUG', true );", "define( 'WP_DEBUG', false );")
# WP_DEBUG_LOG true -> false
c = c.replace("define( 'WP_DEBUG_LOG', true );", "define( 'WP_DEBUG_LOG', false );")
with open(path, "w") as f:
    f.write(c)
print("Done")
'''
b64 = base64.b64encode(script.encode()).decode()
result = subprocess.run(
    ["ssh", "-o", "StrictHostKeyChecking=no", f"{user}@{host}",
     f"echo {b64} | base64 -d | python3"],
    capture_output=True,
    text=True,
    timeout=30,
)
print(result.stdout or result.stderr)
exit(result.returncode)
