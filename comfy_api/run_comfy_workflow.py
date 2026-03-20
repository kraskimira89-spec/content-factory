import json
import time
from pathlib import Path

import requests  # pip install requests

SERVER = "127.0.0.1:8000"  # ComfyUI
WORKFLOW_PATH = Path(r"D:\content-factory\workflow_api.json")

OUTPUT_DIR = Path(r"D:\content-factory\outputs")
HISTORY_DIR = Path(r"D:\content-factory\history")

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
HISTORY_DIR.mkdir(parents=True, exist_ok=True)


def queue_prompt():
    with WORKFLOW_PATH.open("r", encoding="utf-8") as f:
        data = json.load(f)

    if "prompt" in data:
        payload = data
    else:
        payload = {
            "prompt": data,
            "client_id": "content-factory",
        }

    url = f"http://{SERVER}/prompt"
    resp = requests.post(url, json=payload)
    resp.raise_for_status()
    j = resp.json()
    print("queue_prompt response:", j)
    return j["prompt_id"]


def get_history(prompt_id):
    url = f"http://{SERVER}/history/{prompt_id}"
    resp = requests.get(url)
    resp.raise_for_status()
    return resp.json()


def save_history(prompt_id, history_obj):
    path = HISTORY_DIR / f"{prompt_id}.json"
    with path.open("w", encoding="utf-8") as f:
        json.dump(history_obj, f, ensure_ascii=False, indent=2)
    print("History saved to:", path)
    return path


def wait_for_completion(prompt_id, poll_interval=2):
    while True:
        history = get_history(prompt_id)
        entry = history.get(prompt_id, {})
        outputs = entry.get("outputs", {})

        if outputs:
            print("Workflow finished.")
            # сохраняем весь history в файл
            save_history(prompt_id, history)
            return entry

        print("Still running, wait...", prompt_id)
        time.sleep(poll_interval)


def download_image(filename, subfolder, folder_type="output"):
    params = {
        "filename": filename,
        "subfolder": subfolder,
        "type": folder_type,
    }
    url = f"http://{SERVER}/view"
    resp = requests.get(url, params=params)
    resp.raise_for_status()

    out_path = OUTPUT_DIR / filename
    with out_path.open("wb") as f:
        f.write(resp.content)
    print("Saved image:", out_path)
    return out_path


def main():
    print("Queueing prompt...")
    prompt_id = queue_prompt()
    print("Got prompt_id:", prompt_id)

    print("Waiting for completion...")
    entry = wait_for_completion(prompt_id)

    outputs = entry.get("outputs", {})
    for node_id, node_data in outputs.items():
        images = node_data.get("images", [])
        for img in images:
            filename = img["filename"]
            subfolder = img.get("subfolder", "")
            folder_type = img.get("type", "output")
            download_image(filename, subfolder, folder_type)

    print("Done.")


if __name__ == "__main__":
    main()
