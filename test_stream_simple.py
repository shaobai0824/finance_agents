# -*- coding: utf-8 -*-
import requests
import json
import time

url = "http://localhost:8000/query/stream"
data = {
    "query": "30 years old, monthly income 50K, want investment advice",
    "user_profile": {"risk_tolerance": "moderate"}
}

print(f"Start: {time.strftime('%H:%M:%S')}")
start_time = time.time()
first_content_time = None

try:
    response = requests.post(url, json=data, stream=True, timeout=60)

    for line in response.iter_lines():
        if line:
            line_text = line.decode('utf-8')
            if line_text.startswith('data: '):
                data_json = line_text[6:]
                try:
                    event = json.loads(data_json)
                    if event.get('type') == 'content':
                        if first_content_time is None:
                            first_content_time = time.time() - start_time
                            print(f"\n[{first_content_time:.1f}s] FIRST CONTENT RECEIVED!")
                        print(event.get('content', ''), end='', flush=True)
                    elif event.get('type') == 'done':
                        print(f"\n\nDone! Session: {event.get('session_id')}")
                except:
                    pass

except Exception as e:
    print(f"\nError: {e}")

total_time = time.time() - start_time
print(f"\nTotal time: {total_time:.2f}s")
if first_content_time:
    print(f"Time to first content: {first_content_time:.2f}s")
