import json
import re

def find_path(data, target_key, current_path="root"):
    if isinstance(data, dict):
        for k, v in data.items():
            new_path = f"{current_path}['{k}']"
            if k == target_key:
                print(f"FOUND KEY: {new_path} -> {str(v)[:100]}...")
            find_path(v, target_key, new_path)
    elif isinstance(data, list):
        for i, v in enumerate(data):
            new_path = f"{current_path}[{i}]"
            find_path(v, target_key, new_path)

def analyze_dump():
    try:
        content = ""
        with open("tiktok_scripts_dump.txt", "r", encoding="utf-8") as f:
            content = f.read()
            
        # Extract JSON part (naive split based on dump format)
        parts = content.split("--- ID: __UNIVERSAL_DATA_FOR_REHYDRATION__ ---")
        if len(parts) > 1:
            json_text = parts[1].strip()
            # Clean up trailing garbage if any
            try:
                data = json.loads(json_text)
                print("Successfully parsed JSON.")
                print("Searching for 'playAddr'...")
                find_path(data, "playAddr")
            except Exception as e:
                print(f"JSON Parse Error: {e}")
                # Try locating playAddr raw
                idx = json_text.find("playAddr")
                if idx != -1:
                    print(f"Raw context: {json_text[idx-50:idx+100]}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    analyze_dump()
