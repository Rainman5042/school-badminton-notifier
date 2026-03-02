"""
儲存模組 - 管理已通知過的公告紀錄，避免重複通知
使用 JSON 檔案儲存，適合 GitHub Actions 環境
"""
import json
import os
import hashlib
import logging
from typing import List, Dict, Set
from datetime import datetime

import config

logger = logging.getLogger(__name__)

# 最多保留多少筆已通知紀錄（避免檔案無限增長）
MAX_RECORDS = 1000


def _generate_id(announcement: Dict) -> str:
    """
    為公告產生唯一 ID（基於標題 + 學校名稱）
    """
    key = f"{announcement.get('school', '')}:{announcement.get('title', '')}"
    return hashlib.md5(key.encode("utf-8")).hexdigest()


def load_notified() -> Dict:
    """
    載入已通知過的公告紀錄
    """
    os.makedirs(config.DATA_DIR, exist_ok=True)

    if not os.path.exists(config.NOTIFIED_FILE):
        return {"records": {}, "last_run": None}

    try:
        with open(config.NOTIFIED_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            # 相容舊格式
            if isinstance(data, list):
                return {
                    "records": {item: True for item in data},
                    "last_run": None,
                }
            return data
    except (json.JSONDecodeError, IOError) as e:
        logger.warning(f"讀取已通知紀錄失敗，將重新建立: {e}")
        return {"records": {}, "last_run": None}


def save_notified(data: Dict):
    """
    儲存已通知過的公告紀錄（含清理過舊資料）
    """
    os.makedirs(config.DATA_DIR, exist_ok=True)

    # 如果紀錄太多，保留最新的
    records = data.get("records", {})
    if len(records) > MAX_RECORDS:
        # 按照加入時間排序，保留最新的
        sorted_records = sorted(
            records.items(),
            key=lambda x: x[1].get("timestamp", "") if isinstance(x[1], dict) else "",
            reverse=True,
        )
        data["records"] = dict(sorted_records[:MAX_RECORDS])

    data["last_run"] = datetime.now().isoformat()

    try:
        with open(config.NOTIFIED_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        logger.debug(f"已儲存 {len(data['records'])} 筆通知紀錄")
    except IOError as e:
        logger.error(f"儲存已通知紀錄失敗: {e}")


def filter_new_announcements(announcements: List[Dict]) -> List[Dict]:
    """
    過濾掉已經通知過的公告，只回傳新的
    """
    data = load_notified()
    records = data.get("records", {})

    new_announcements = []
    for ann in announcements:
        ann_id = _generate_id(ann)
        if ann_id not in records:
            new_announcements.append(ann)

    logger.info(
        f"共 {len(announcements)} 則匹配公告，"
        f"其中 {len(new_announcements)} 則為新公告"
    )
    return new_announcements


def mark_as_notified(announcements: List[Dict]):
    """
    將公告標記為已通知
    """
    data = load_notified()
    records = data.get("records", {})

    for ann in announcements:
        ann_id = _generate_id(ann)
        records[ann_id] = {
            "title": ann.get("title", ""),
            "school": ann.get("school", ""),
            "url": ann.get("url", ""),
            "timestamp": datetime.now().isoformat(),
        }

    data["records"] = records
    save_notified(data)
    logger.info(f"已將 {len(announcements)} 則公告標記為已通知")
