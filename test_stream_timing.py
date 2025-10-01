import requests
import json
import time

url = "http://localhost:8000/query/stream"
data = {
    "query": "我30歲，月收入5萬，想投資理財，請給建議",
    "user_profile": {"risk_tolerance": "moderate"}
}

print(f"=== 開始: {time.strftime('%H:%M:%S')} ===")
start_time = time.time()
first_content_received = False

try:
    response = requests.post(url, json=data, stream=True, timeout=60)

    for line in response.iter_lines():
        if line:
            line_text = line.decode('utf-8')
            if line_text.startswith('data: '):
                data_json = line_text[6:]  # 移除 'data: ' 前綴
                try:
                    event = json.loads(data_json)
                    if event.get('type') == 'content':
                        elapsed = int(time.time() - start_time)
                        if not first_content_received:
                            print(f"\n[{elapsed}秒] 🎉 收到第一個內容塊！")
                            first_content_received = True
                        print(f"[{elapsed}秒] {event.get('content', '')}", end='', flush=True)
                    elif event.get('type') == 'done':
                        elapsed = int(time.time() - start_time)
                        print(f"\n\n[{elapsed}秒] ✅ 完成！")
                        print(f"session_id: {event.get('session_id')}")
                except json.JSONDecodeError:
                    pass

except Exception as e:
    print(f"\n❌ 錯誤: {e}")

total_time = time.time() - start_time
print(f"\n總處理時間: {total_time:.2f} 秒")
