import os
import sys
import json
import requests

# Ensure UTF-8 console output
try:
    sys.stdout.reconfigure(encoding='utf-8')
except:
    pass

def test_api():
    print("=== CHẨN ĐOÁN KẾT NỐI API DONUT BROWSER ===")
    
    # 1. Đọc config
    try:
        import config
    except ImportError:
        print("✗ Không tìm thấy file config.py trong thư mục.")
        return
        
    api_url = getattr(config, "DONUT_API_URL", "http://127.0.0.1:10108")
    api_key = getattr(config, "DONUT_API_KEY", "")
    
    print(f"Cấu hình hiện tại:")
    print(f"  - API URL: {api_url}")
    print(f"  - API Key: {api_key[:10]}... (Độ dài: {len(api_key)})" if api_key else "  - API Key: CHƯA ĐIỀN (Vui lòng điền và lưu trong GUI/config)")
    
    if not api_key:
        print("\n⚠ Vui lòng mở GiaanTesttool.py, nhập API Key của Donut Browser, nhấn '✔ Test' để tool tự động lưu cấu hình, sau đó chạy lại script này.")
        return

    # 2. Gọi API lấy danh sách profiles
    url = f"{api_url.rstrip('/')}/v1/profiles"
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {api_key}'
    }
    
    print(f"\nĐang gọi GET {url}...")
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        print(f"HTTP Status: {resp.status_code}")
        
        try:
            data = resp.json()
            # Lưu raw JSON ra file
            output_file = "donut_profiles_response.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print(f"✔ Đã ghi nhận phản hồi vào file: {output_file}")
            
            # Phân tích dữ liệu
            print("\nPhân tích cấu trúc dữ liệu:")
            print(f"  - Kiểu dữ liệu gốc: {type(data).__name__}")
            if isinstance(data, list):
                print(f"  - Số lượng profile trực tiếp: {len(data)}")
                if len(data) > 0:
                    print("  - Keys của profile đầu tiên:", list(data[0].keys()))
                    print("  - Dữ liệu mẫu:", json.dumps(data[0], ensure_ascii=False, indent=2))
            elif isinstance(data, dict):
                print(f"  - Các keys ở mức cao nhất: {list(data.keys())}")
                for k, v in data.items():
                    if isinstance(v, list):
                        print(f"    + Key '{k}' chứa list có {len(v)} phần tử")
                        if len(v) > 0:
                            print(f"    + Keys của phần tử đầu tiên trong '{k}':", list(v[0].keys()))
                    else:
                        # Rút gọn giá trị dài
                        val_str = str(v)
                        if len(val_str) > 60:
                            val_str = val_str[:60] + "..."
                        print(f"    + Key '{k}': {val_str} (kiểu: {type(v).__name__})")
            else:
                print("  - Phản hồi không phải list hay dict.")
                
        except json.JSONDecodeError:
            print("✗ Phản hồi không phải định dạng JSON hợp lệ.")
            print(f"Raw Response:\n{resp.text[:500]}")
            
    except requests.RequestException as e:
        print(f"✗ Lỗi kết nối tới API: {e}")

if __name__ == "__main__":
    test_api()
