import json

def recursive_keys(d, path=""):
    if isinstance(d, dict):
        for k, v in d.items():
            new_path = f"{path}.{k}" if path else k
            print(new_path)
            recursive_keys(v, new_path)
    elif isinstance(d, list):
        for i, v in enumerate(d):
            new_path = f"{path}[{i}]"
            recursive_keys(v, new_path)

try:
    with open('tiktok_debug_data.json', encoding='utf-8') as f:
        data = json.load(f)
        # Chỉ in 2 level đầu để tránh spam
        if 'universal' in data and data['universal']:
             print("UNIVERSAL DATA KEYS:")
             for k in data['universal']:
                 print(f"- {k}")
                 obj = data['universal'][k]
                 if isinstance(obj, dict):
                     for subk in obj:
                         print(f"  - {subk}")
        else:
             print("Universal data is empty or missing")
             
except Exception as e:
    print(e)
