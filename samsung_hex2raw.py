#!/usr/bin/env python3
import sys
import argparse

# Dictionary of standard Samsung 32-bit codes
SAMSUNG_CODES = {
    "Power": "E0E040BF",
    "Settings (Menu)": "E0E058A7",
    "Home (Smart Hub)": "E0E09E61",
    "Back (Return)": "E0E01AE5",
    "Up": "E0E006F9",
    "Down": "E0E08679",
    "Left": "E0E0A659",
    "Right": "E0E046B9",
    "OK (Enter)": "E0E016E9",
    "Volume +": "E0E0E01F",
    "Volume -": "E0E0D02F",
    "Mute": "E0E0F00F",
    "Channel Up": "E0E048B7",
    "Channel Down": "E0E008F7",
    "Play": "E0E0E21D",
    "Pause": "E0E052AD"
}

def hex_to_samsung_raw(hex_code):
    """
    Converts a 32-bit Samsung Hex code into its raw timing sequence in microseconds.
    Samsung Protocol:
      - Header: 4500us mark, 4500us space
      - Bit 0: 560us mark, 560us space
      - Bit 1: 560us mark, 1690us space
      - Stop Bit: 560us mark
      - Carrier Frequency: ~38.4kHz (38000 to 38400 Hz)
    """
    hex_code = hex_code.replace("0x", "").strip().upper()
    if len(hex_code) != 8:
        raise ValueError(f"Samsung hex code must be exactly 8 characters (32 bits). Got: {hex_code}")
        
    raw_timings = [4500, 4500]
    
    # Process the 4 bytes (e.g., E0, E0, 40, BF)
    for i in range(0, 8, 2):
        byte_str = hex_code[i:i+2]
        byte_val = int(byte_str, 16)
        
        # Samsung protocol transmits the Least Significant Bit (LSB) first for each byte
        for bit_idx in range(8):
            bit = (byte_val >> bit_idx) & 1
            raw_timings.append(560)  # Pulse/Mark
            if bit == 1:
                raw_timings.append(1690) # Space for '1'
            else:
                raw_timings.append(560)  # Space for '0'
                
    # End of transmission stop bit (mark)
    raw_timings.append(560)
    
    return raw_timings

def main():
    parser = argparse.ArgumentParser(description="Convert Samsung 32-bit Hex (e.g. E0E040BF) to raw timings (38.4kHz).")
    parser.add_argument("hexcode", type=str, nargs="?", help="A specific 32-bit hex code to convert (e.g. E0E040BF)")
    parser.add_argument("--all", action="store_true", help="Print raw timings for all standard Samsung codes")
    
    args = parser.parse_args()
    
    if args.all:
        print("=== Samsung IR Raw Timings (38.4kHz) ===\n")
        for name, code in SAMSUNG_CODES.items():
            raw = hex_to_samsung_raw(code)
            raw_str = " ".join(map(str, raw))
            print(f"[{name}] (Code: {code})")
            print(f"{raw_str}\n")
    elif args.hexcode:
        raw = hex_to_samsung_raw(args.hexcode)
        print(" ".join(map(str, raw)))
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
