#!/usr/bin/env python3
import sys
import json
import uuid
import argparse
from samsung_hex2raw import SAMSUNG_CODES, hex_to_samsung_raw

def main():
    parser = argparse.ArgumentParser(description="Add all standard Samsung buttons to the JSON backup.")
    parser.add_argument("--file", type=str, default="irblaster_backup_1783825408844.json", help="Path to JSON backup")
    parser.add_argument("--remote", type=str, default="Samsung TV", help="Name of the remote to add to (creates if missing)")
    args = parser.parse_args()

    json_file = args.file
    remote_name = args.remote

    # 1. Load JSON
    try:
        with open(json_file, "r") as f:
            data = json.load(f)
    except Exception as e:
        print(f"Error loading {json_file}: {e}")
        sys.exit(1)

    remotes = data.get("remotes", [])
    
    # 2. Find or create remote
    target_remote = next((r for r in remotes if r.get("name") == remote_name), None)
    if not target_remote:
        print(f"Creating new remote: {remote_name}")
        new_id = max([r.get("id", 0) for r in remotes] + [0]) + 1
        target_remote = {
            "id": new_id,
            "buttons": [],
            "name": remote_name,
            "useNewStyle": False
        }
        data.setdefault("remotes", []).append(target_remote)
    else:
        print(f"Adding to existing remote: {remote_name} (clearing old buttons)")
        target_remote["buttons"] = []

    # 3. Add all buttons
    added_count = 0
    for name, hex_code in SAMSUNG_CODES.items():
        # Format the image/button name safely for the IR Blaster
        img_name = name.lower() \
            .replace(" ", "_") \
            .replace("+", "up") \
            .replace("-", "down") \
            .replace("/", "_") \
            .replace("(", "") \
            .replace(")", "") \
            .replace("__", "_") \
            .strip("_")
            
        # Clean up some of the dual names
        if img_name == "ok_enter": img_name = "ok"
        if img_name == "settings_menu": img_name = "menu"
        if img_name == "home_smart_hub": img_name = "home"
        if img_name == "back_return": img_name = "back"
        
        new_button = {
            "id": str(uuid.uuid4()),
            "code": None,
            "rawData": None,
            "frequency": 38400,
            "image": img_name,
            "isImage": False,
            "necBitOrder": None,
            "protocol": "necx2",
            "protocolParams": {
                "hex": hex_code
            },
            "iconCodePoint": None,
            "iconFontFamily": None,
            "iconFontPackage": None,
            "iconColor": None,
            "buttonColor": None
        }
        
        target_remote.setdefault("buttons", []).append(new_button)
        added_count += 1
        print(f"  + Added button: {name} ({hex_code}) as '{img_name}' (necx2)")

    # 4. Save JSON
    with open(json_file, "w") as f:
        json.dump(data, f, separators=(',', ':'))

    print(f"\nSuccessfully added {added_count} buttons to remote '{remote_name}' in {json_file}.")

if __name__ == "__main__":
    main()
