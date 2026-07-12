#!/usr/bin/env python3
import sys
import json
import uuid
import os
from pronto2raw import convert_pronto_to_raw

def main():
    print("=== IR Blaster JSON Button Adder ===")
    
    # 1. Get JSON file
    default_file = "irblaster_backup_1783825408844.json"
    json_file = input(f"1) Enter the JSON backup file to modify [default: {default_file}]: ").strip()
    if not json_file:
        json_file = default_file
        
    if not os.path.exists(json_file):
        print(f"Error: File '{json_file}' does not exist.")
        sys.exit(1)
        
    try:
        with open(json_file, "r") as f:
            data = json.load(f)
    except json.JSONDecodeError:
        print(f"Error: Failed to parse JSON from '{json_file}'.")
        sys.exit(1)

    # 2. Get Remote Name
    remotes = data.get("remotes", [])
    remote_names = [r.get("name", "Unknown") for r in remotes]
    print(f"\nExisting remotes: {', '.join(remote_names) if remote_names else 'None'}")
    
    remote_name = input("2) Enter the remote name to add the button to (will create new if it doesn't exist): ").strip()
    if not remote_name:
        print("Error: Remote name cannot be empty.")
        sys.exit(1)
        
    # 3. Get Button Name
    button_name = input("3) Enter the name of the button (e.g. 'volume_up'): ").strip()
    if not button_name:
        print("Error: Button name cannot be empty.")
        sys.exit(1)
        
    # 4. Get Pronto Code
    pronto_code = input("4) Enter the Pronto Hex code: ").strip()
    if not pronto_code:
        print("Error: Pronto Hex code cannot be empty.")
        sys.exit(1)

    # 5. Process the Pronto Code
    print("\nProcessing Pronto Hex...")
    words = [int(w, 16) for w in pronto_code.split()]
    if len(words) < 4 or words[0] != 0:
        print("Error: Invalid Pronto Hex code. Make sure it starts with 0000.")
        sys.exit(1)
        
    freq_code = words[1]
    frequency = int(round(1000000 / (freq_code * 0.241246))) if freq_code > 0 else 38000
    
    # Convert and format cleanly using the generic protocol detector
    raw_timings = convert_pronto_to_raw(pronto_code, clean=True)
    if not raw_timings:
        print("Error: Failed to convert timings.")
        sys.exit(1)
        
    raw_data_str = " ".join(map(str, raw_timings))

    # 6. Find or Create Remote
    target_remote = next((r for r in remotes if r.get("name") == remote_name), None)
    
    if not target_remote:
        print(f"Remote '{remote_name}' not found. Creating a new remote...")
        new_id = max([r.get("id", 0) for r in remotes] + [0]) + 1
        target_remote = {
            "id": new_id,
            "buttons": [],
            "name": remote_name,
            "useNewStyle": False
        }
        data.setdefault("remotes", []).append(target_remote)
    else:
        print(f"Found existing remote '{remote_name}'.")

    # 7. Create and Append Button
    new_button = {
        "id": str(uuid.uuid4()),
        "code": None,
        "rawData": raw_data_str,
        "frequency": frequency,
        "image": button_name,
        "isImage": False,
        "necBitOrder": None,
        "protocol": None,
        "protocolParams": None,
        "iconCodePoint": None,
        "iconFontFamily": None,
        "iconFontPackage": None,
        "iconColor": None,
        "buttonColor": None
    }
    
    target_remote.setdefault("buttons", []).append(new_button)

    # 8. Save JSON
    with open(json_file, "w") as f:
        json.dump(data, f, separators=(',', ':'))
        
    print(f"\nSuccess! Button '{button_name}' has been added to remote '{remote_name}'.")
    print(f"File '{json_file}' has been successfully updated.")

if __name__ == "__main__":
    main()
