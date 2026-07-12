import json
import uuid
import datetime
from samsung_hex2raw import SAMSUNG_CODES, hex_to_samsung_raw

def to_pronto(raw_timings, freq=38400):
    w1 = int(round(1000000 / (freq * 0.241246)))
    unit = w1 * 0.241246
    
    # Ensure even number of elements (pairs)
    if len(raw_timings) % 2 != 0:
        raw_timings.append(30000)
        
    num_pairs = len(raw_timings) // 2
    
    pronto = [0x0000, w1, num_pairs, 0x0000]
    for t in raw_timings:
        pronto.append(int(round(t / unit)))
        
    return " ".join([f"{x:04X}" for x in pronto])

def convert_to_hair_raw(raw_timings):
    hair_raw = []
    # Work on a copy to avoid mutating the original if we append
    working_timings = list(raw_timings)
    if len(working_timings) % 2 != 0:
        working_timings.append(30000)
        
    for i, val in enumerate(working_timings):
        if i % 2 == 1:
            hair_raw.append(-val) # spaces are negative in Home Assistant / HAIR
        else:
            hair_raw.append(val)
    return hair_raw

def main():
    with open('hair_codes.json', 'r') as f:
        data = json.load(f)
        
    devices = data.get("data", {}).get("devices", [])
    
    # Check if Samsung TV exists, if not create it
    samsung_device = next((d for d in devices if d.get("name") == "Samsung TV"), None)
    if not samsung_device:
        print("Creating new Samsung TV device in HAIR")
        # Copy emitters from the first device we can find
        hisense = next((d for d in devices if d.get("name") == "Hisense"), None)
        emitter_entity_ids = hisense.get("emitter_entity_ids", []) if hisense else []
        capture_device_id = hisense.get("capture_device_id", None) if hisense else None
        
        samsung_device = {
            "id": str(uuid.uuid4()),
            "name": "Samsung TV",
            "device_type": "media_player",
            "manufacturer": "Samsung",
            "model": None,
            "emitter_entity_ids": emitter_entity_ids,
            "capture_device_id": capture_device_id,
            "capture_provider_type": "native",
            "commands": [],
            "database_id": None,
            "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "updated_at": datetime.datetime.now(datetime.timezone.utc).isoformat()
        }
        devices.append(samsung_device)
    else:
        print("Updating existing Samsung TV device in HAIR")
        samsung_device["commands"] = []
        samsung_device["updated_at"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
        
    added = 0
    for name, hex_code in SAMSUNG_CODES.items():
        raw_timings = hex_to_samsung_raw(hex_code)
        
        pronto_str = to_pronto(list(raw_timings), 38400)
        hair_raw = convert_to_hair_raw(raw_timings)
        
        # Format: E0E040BF
        address = int(hex_code[0:4], 16)
        command = int(hex_code[4:6], 16)
        
        # Normalize category
        category = "custom"
        name_lower = name.lower()
        if "power" in name_lower: category = "power"
        elif "volume" in name_lower or "mute" in name_lower: category = "volume"
        elif "channel" in name_lower: category = "channel"
        elif "play" in name_lower or "pause" in name_lower: category = "media_control"
        elif "up" in name_lower or "down" in name_lower or "left" in name_lower or "right" in name_lower or "ok" in name_lower or "back" in name_lower:
            category = "navigation"
        
        cmd = {
            "id": str(uuid.uuid4()),
            "name": name.split(" (")[0], # E.g. "Settings (Menu)" -> "Settings"
            "category": category,
            "source": "imported",
            "protocol": "PRONTO",
            "code": pronto_str,
            "raw_timings": hair_raw,
            "frequency": 38400,
            "repeat_count": 1,
            "send_count": 1,
            "byte_hash": None,
            "decoded_protocol": "Samsung",
            "decoded_address": address,
            "decoded_command": command,
            "decoded_fingerprint": f"Samsung:{hex(address)}:{hex(command)}",
            "tx_force_raw": False,
            "plucked_command_name": None,
            "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat()
        }
        samsung_device["commands"].append(cmd)
        added += 1
        print(f" + Added {name} (Category: {category})")
        
    with open('hair_codes.json', 'w') as f:
        json.dump(data, f, indent=4)
        
    print(f"Successfully added {added} Samsung codes to hair_codes.json")
        
if __name__ == "__main__":
    main()
