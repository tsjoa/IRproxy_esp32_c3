#!/usr/bin/env python3
import sys
import json
import uuid
import argparse
from pronto2raw import convert_pronto_to_raw

def main():
    parser = argparse.ArgumentParser(description="Add a button with a converted Pronto Hex code to the IR Blaster JSON backup.")
    parser.add_argument("buttonname", type=str, help="Name of the button (e.g. 'volume_up')")
    parser.add_argument("prontocode", type=str, help="The Pronto Hex string (enclose in quotes)")
    parser.add_argument("--file", type=str, default="irblaster_backup_1783825408844.json", help="Path to the JSON backup file")
    
    args = parser.parse_args()
    
    # 1. Parse Pronto Hex to get raw timings and frequency
    words = [int(w, 16) for w in args.prontocode.strip().split()]
    if len(words) < 4 or words[0] != 0:
        print("Error: Invalid Pronto Hex code.")
        sys.exit(1)
        
    freq_code = words[1]
    frequency = int(round(1000000 / (freq_code * 0.241246))) if freq_code > 0 else 38000
    
    # Use clean=True to leverage the automatic protocol detection and reconstruction
    raw_timings = convert_pronto_to_raw(args.prontocode, clean=True)
    raw_data_str = " ".join(map(str, raw_timings))
    
    # 2. Load JSON
    try:
        with open(args.file, "r") as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"Error: File {args.file} not found.")
        sys.exit(1)
    except json.JSONDecodeError:
        print(f"Error: Failed to parse JSON from {args.file}.")
        sys.exit(1)
        
    # 3. Create the new button object
    new_button = {
        "id": str(uuid.uuid4()),
        "code": None,
        "rawData": raw_data_str,
        "frequency": frequency,
        "image": args.buttonname,
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
    
    # 4. Append to the last remote (which is "jvc" in the provided file)
    if not data.get("remotes"):
        print("Error: No remotes found in the JSON file.")
        sys.exit(1)
        
    target_remote = data["remotes"][-1]
    target_remote.setdefault("buttons", []).append(new_button)
    
    # 5. Save JSON
    with open(args.file, "w") as f:
        json.dump(data, f, separators=(',', ':'))  # using compact formatting similar to the original file
        
    print(f"Successfully added button '{args.buttonname}' to remote '{target_remote.get('name', 'Unknown')}'.")
    print(f"File '{args.file}' updated.")

if __name__ == "__main__":
    main()
