#!/usr/bin/env python3
import sys
import argparse

def is_match(val, expected, tolerance=0.25):
    """Check if a timing value matches the expected value within a tolerance."""
    return expected * (1 - tolerance) <= val <= expected * (1 + tolerance)

def format_bits_to_hex(bits):
    if not bits:
        return ""
    # Group into bytes (assume LSB first which is common for NEC/JVC)
    bytes_list = []
    for i in range(0, len(bits), 8):
        chunk = bits[i:i+8]
        val = sum(b << j for j, b in enumerate(chunk))
        bytes_list.append(f"{val:02X}")
    return " ".join(bytes_list)

def identify_and_reconstruct(raw_timings):
    """
    Attempts to identify the IR protocol and reconstructs a perfectly 
    aligned timing array. Returns (ProtocolName, ReconstructedTimings, DecodedHex).
    """
    if len(raw_timings) < 4:
        return None, None, None
        
    header_mark = raw_timings[0]
    header_space = raw_timings[1]
    
    # Count the number of bits (pairs - header - stop bit)
    num_bits = (len(raw_timings) - 3) // 2
    
    # 1. Check JVC (16 bits typically, 8400/4200 header)
    if num_bits == 16 and is_match(header_mark, 8400, 0.15) and is_match(header_space, 4200, 0.15):
        base_tick = 525
        reconstructed = [8400, 4200]
        bits = []
        for i in range(2, len(raw_timings)-1, 2):
            mark = raw_timings[i]
            space = raw_timings[i+1]
            if is_match(space, 525, 0.4):
                reconstructed.extend([base_tick, base_tick])
                bits.append(0)
            elif is_match(space, 1575, 0.4):
                reconstructed.extend([base_tick, base_tick * 3])
                bits.append(1)
            else:
                break
        reconstructed.append(base_tick) # Stop bit
        reconstructed.append(21000)     # Standard JVC trailing gap
        
        # JVC mandates sending the frame twice
        reconstructed = reconstructed + reconstructed
        return "JVC", reconstructed, format_bits_to_hex(bits)

    # 2. Check NEC (32 bits typically, 9000/4500 header)
    if num_bits == 32 and is_match(header_mark, 9000, 0.15) and is_match(header_space, 4500, 0.15):
        base_tick = 562
        reconstructed = [9000, 4500]
        bits = []
        for i in range(2, len(raw_timings)-1, 2):
            mark = raw_timings[i]
            space = raw_timings[i+1]
            if is_match(space, 562, 0.4):
                reconstructed.extend([base_tick, base_tick])
                bits.append(0)
            elif is_match(space, 1687, 0.4):
                reconstructed.extend([base_tick, base_tick * 3])
                bits.append(1)
            else:
                break
        reconstructed.append(base_tick) # Stop bit
        return "NEC", reconstructed, format_bits_to_hex(bits)

    # 3. Check Samsung (32 bits typically, 4500/4500 header)
    if num_bits == 32 and is_match(header_mark, 4500, 0.2) and is_match(header_space, 4500, 0.2):
        base_tick = 560
        reconstructed = [4500, 4500]
        bits = []
        for i in range(2, len(raw_timings)-1, 2):
            mark = raw_timings[i]
            space = raw_timings[i+1]
            if is_match(space, 560, 0.4):
                reconstructed.extend([base_tick, base_tick])
                bits.append(0)
            elif is_match(space, 1690, 0.4):
                reconstructed.extend([base_tick, 1690])
                bits.append(1)
            else:
                break
        reconstructed.append(base_tick) # Stop bit
        return "Samsung", reconstructed, format_bits_to_hex(bits)
        
    # 4. Check Sony (SIRC) (12, 15, or 20 bits, 2400/600 header)
    if num_bits in (12, 15, 20) and is_match(header_mark, 2400, 0.2) and is_match(header_space, 600, 0.25):
        base_tick = 600
        reconstructed = [2400, 600]
        bits = []
        for i in range(2, len(raw_timings)-1, 2):
            mark = raw_timings[i]
            space = raw_timings[i+1]
            if is_match(mark, 600, 0.4):
                reconstructed.extend([base_tick, base_tick])
                bits.append(0)
            elif is_match(mark, 1200, 0.4):
                reconstructed.extend([base_tick * 2, base_tick])
                bits.append(1)
            else:
                break
        return "Sony", reconstructed, format_bits_to_hex(bits)

    # Unknown protocol
    return None, None, None


def convert_pronto_to_raw(pronto_hex, clean=False, jvc_repeat=False):
    """
    Converts a Pronto Hex string into raw timing arrays in microseconds.
    Optionally auto-recognizes and reconstructs standard protocols.
    """
    words = [int(w, 16) for w in pronto_hex.strip().split()]
    
    if len(words) < 4:
        raise ValueError("Invalid Pronto Hex: too short. Must have at least a 4-word header.")
        
    if words[0] != 0x0000:
        raise ValueError("Only raw learned Pronto Hex (starts with 0000) is supported.")
        
    # Calculate carrier frequency factor
    factor = words[1] * 0.241246
    
    seq1_len = words[2] * 2
    seq2_len = words[3] * 2
    
    data_words = words[4 : 4 + seq1_len + seq2_len]
    raw_timings = [int(round(val * factor)) for val in data_words]
    
    if clean:
        protocol, reconstructed, hex_data = identify_and_reconstruct(raw_timings)
        if protocol:
            print(f"[*] Decoded Protocol: {protocol}")
            print(f"[*] Decoded Hex Data (LSB First): {hex_data}")
            return reconstructed
        else:
            print("[!] Protocol not recognized. Applying generic mathematical clean.")
            # Fallback to simple quantization
            if raw_timings:
                base_tick = min([t for t in raw_timings if t > 100])
                base_ticks = [t for t in raw_timings if t < base_tick * 1.5]
                
                if base_ticks:
                    avg_base = sum(base_ticks) / len(base_ticks)
                    avg_base = round(avg_base / 25) * 25
                    if avg_base == 0: 
                        avg_base = base_tick
                        
                    raw_timings = [int(round(t / avg_base) * avg_base) for t in raw_timings]
    
    return raw_timings

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Convert Pronto Hex IR code into raw timings with automatic protocol recognition.")
    parser.add_argument("code", type=str, nargs="?", help="The Pronto Hex string. Enclose in quotes.")
    parser.add_argument("--raw", action="store_true", help="Print the uncleaned mathematical conversion.")
    args = parser.parse_args()

    if args.code:
        hex_code = args.code
    else:
        print("No code provided. Using default JVC example code...\n")
        hex_code = "0000 006D 0012 0000 0143 009E 0016 003A 0016 003A 0016 0012 0016 0012 0016 0012 0016 003A 0016 0012 0016 003A 0016 0012 0016 003A 0016 003A 0015 003B 0016 003A 0016 0012 0016 0012 0016 0012 0016 0475"
    
    if args.raw:
        print("--- Exact Mathematical Conversion ---")
        raw = convert_pronto_to_raw(hex_code, clean=False)
        print(" ".join(map(str, raw)))
    else:
        print("--- Cleaned / Decoded Output ---")
        clean_raw = convert_pronto_to_raw(hex_code, clean=True)
        print(" ".join(map(str, clean_raw)))
