#!/usr/bin/env python3
import json
import uuid
import argparse

def main():
    parser = argparse.ArgumentParser(description="Extract captured codes from HAIR format and backport them to Android IR Blaster export format.")
    parser.add_argument("--input", type=str, default="hair_codes2.json", help="Path to the HAIR JSON file")
    parser.add_argument("--output", type=str, default="irblaster_hair_export.json", help="Output path for the IR Blaster export file")
    
    args = parser.parse_args()

    # Load the HAIR JSON format
    try:
        with open(args.input, 'r') as f:
            hair_data = json.load(f)
    except FileNotFoundError:
        print(f"Error: Could not find input file '{args.input}'")
        return

    new_remotes = []

    # Parse devices out of the hair config
    for dev in hair_data.get("data", {}).get("devices", []):
        dev_name = dev.get("name", "Unknown Device")
        cmds = dev.get("commands", [])
        
        new_buttons = []
        for cmd in cmds:
            cmd_name = cmd.get("name", "Unknown Button")
            raw_timings = cmd.get("raw_timings", [])
            frequency = cmd.get("frequency", 38000)
            
            if not raw_timings:
                continue
                
            # Convert raw_timings to space-separated string of absolute values
            raw_data_str = " ".join(str(abs(x)) for x in raw_timings)
            
            new_button = {
                "id": str(uuid.uuid4()),
                "code": None,
                "rawData": raw_data_str,
                "frequency": frequency,
                "image": cmd_name,
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
            new_buttons.append(new_button)
        
        new_remote = {
            "name": f"{dev_name} (HAIR)",
            "useNewStyle": False,
            "buttons": new_buttons
        }
        new_remotes.append(new_remote)

    # Create the export payload matching IR Blaster's structure
    export_data = {
        "remotes": new_remotes
    }

    # Dump the payload
    with open(args.output, 'w') as f:
        json.dump(export_data, f, separators=(',', ':'))

    print(f"Successfully exported {len(new_remotes)} remotes to {args.output}:")
    for r in new_remotes:
        print(f" - {r['name']} ({len(r['buttons'])} buttons)")

if __name__ == "__main__":
    main()
