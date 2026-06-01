import json

def search_slideshow_json():
    with open("slideshow_debug.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    
    def find_keys(obj, target_keys, path="root", results=None):
        if results is None:
            results = []
        
        if isinstance(obj, dict):
            for k, v in obj.items():
                new_path = f"{path}['{k}']"
                if k in target_keys:
                    results.append((new_path, k, str(v)[:200]))
                find_keys(v, target_keys, new_path, results)
        elif isinstance(obj, list):
            for i, v in enumerate(obj):
                new_path = f"{path}[{i}]"
                find_keys(v, target_keys, new_path, results)
        
        return results
    
    # Search for relevant keys
    targets = ["video", "playAddr", "downloadAddr", "imagePost", "images", "music"]
    results = find_keys(data, targets)
    
    print(f"Found {len(results)} matches:")
    for path, key, value in results:
        print(f"\n{key} at {path}:")
        print(f"  Value: {value}...")

if __name__ == "__main__":
    search_slideshow_json()
