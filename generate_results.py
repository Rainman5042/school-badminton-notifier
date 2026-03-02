#!/usr/bin/env python3
"""
生成靜態結果 JSON 供 GitHub Pages 儀表板使用
此腳本由 GitHub Actions 在每次檢查後執行
"""
import json
import os
import sys

# 確保可以匯入 main 模組
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from main import run


def generate_results():
    """執行檢查並將結果輸出為 docs/results.json"""
    # 以 dry_run=True, force=True 執行完整掃描，顯示所有匹配結果
    # 實際通知由主排程 workflow 負責，這邊只產生結果 JSON
    result = run(dry_run=False, force=True)

    if result is None:
        result = {
            "status": "error",
            "message": "執行結果為空",
            "timestamp": "",
            "total_fetched": 0,
            "after_date_filter": 0,
            "keyword_matched": 0,
            "new_announcements": [],
            "all_matched": [],
        }

    # 清理不可序列化的欄位（date_parsed 等 datetime 物件）
    for key in ("new_announcements", "all_matched"):
        items = result.get(key, [])
        clean_items = []
        for ann in items:
            clean = {k: v for k, v in ann.items() if k != "date_parsed"}
            clean_items.append(clean)
        result[key] = clean_items

    # 確保 docs 目錄存在
    docs_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "docs")
    os.makedirs(docs_dir, exist_ok=True)

    output_path = os.path.join(docs_dir, "results.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"✅ 結果已寫入 {output_path}")
    print(f"   爬取公告: {result.get('total_fetched', 0)} 則")
    print(f"   30天內: {result.get('after_date_filter', 0)} 則")
    print(f"   關鍵字命中: {result.get('keyword_matched', 0)} 則")
    print(f"   新公告: {len(result.get('new_announcements', []))} 則")


if __name__ == "__main__":
    generate_results()
