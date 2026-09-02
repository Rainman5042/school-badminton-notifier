#!/usr/bin/env python3
"""
手動測試 Teams Webhook 是否能正確運作，繞過爬蟲/關鍵字比對，
送出多筆測試公告，驗證是否會彙整成單一張 Adaptive Card。
"""
from datetime import datetime

from notifier import send_teams

if __name__ == "__main__":
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    test_announcements = [
        {
            "school": "測試學校 A",
            "title": f"[測試 1/3] Teams Webhook 合併卡片測試 - {timestamp}",
            "url": "https://example.com/1",
            "matched_keywords": ["測試", "場地"],
        },
        {
            "school": "測試學校 B",
            "title": f"[測試 2/3] Teams Webhook 合併卡片測試 - {timestamp}",
            "url": "https://example.com/2",
            "matched_keywords": ["羽球"],
        },
        {
            "school": "測試學校 C",
            "title": f"[測試 3/3] Teams Webhook 合併卡片測試 - {timestamp}",
            "url": "",
            "matched_keywords": [],
        },
    ]

    ok = send_teams(test_announcements)
    print("✅ 發送成功，請到 Teams 頻道確認是否收到「一張」包含 3 則公告的卡片" if ok else "❌ 發送失敗，請查看上方 log")
