#!/usr/bin/env python3
"""
Web 儀表板 - 提供手動檢查功能的網頁介面
"""
import sys
import logging
import threading
import json
from datetime import datetime

from flask import Flask, render_template, jsonify, request

import config
from main import run

# ========== 日誌設定 ==========
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("web")

app = Flask(__name__)

# 全域狀態：追蹤當前是否正在執行檢查
_check_lock = threading.Lock()
_is_checking = False
_last_result = None


def _serialize_result(result: dict) -> dict:
    """將執行結果序列化為 JSON 安全格式"""
    if result is None:
        return None

    safe = dict(result)

    # 清理公告列表中的 datetime 物件
    for key in ("new_announcements", "all_matched"):
        items = safe.get(key, [])
        clean_items = []
        for ann in items:
            clean = {k: v for k, v in ann.items() if k != "date_parsed"}
            clean_items.append(clean)
        safe[key] = clean_items

    return safe


@app.route("/")
def index():
    """主頁面"""
    return render_template("index.html")


@app.route("/api/check", methods=["POST"])
def api_check():
    """手動觸發檢查的 API"""
    global _is_checking, _last_result

    if _is_checking:
        return jsonify({"error": "檢查正在進行中，請稍候..."}), 429

    data = request.get_json(silent=True) or {}
    dry_run = data.get("dry_run", True)  # Web 預設 dry-run
    force = data.get("force", True)  # Web 預設顯示所有

    with _check_lock:
        _is_checking = True

    try:
        result = run(dry_run=dry_run, force=force)
        _last_result = _serialize_result(result)
        return jsonify(_last_result)
    except Exception as e:
        logger.error(f"手動檢查失敗: {e}", exc_info=True)
        return jsonify({"error": str(e), "status": "error"}), 500
    finally:
        with _check_lock:
            _is_checking = False


@app.route("/api/status")
def api_status():
    """取得狀態"""
    return jsonify({
        "is_checking": _is_checking,
        "last_result": _last_result,
        "schools": [s["name"] for s in config.SCHOOLS],
        "keywords": config.KEYWORDS,
        "school_count": len(config.SCHOOLS),
    })


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 5000
    print(f"\n🏸 羽球場地公告監控 - Web 儀表板")
    print(f"   http://localhost:{port}\n")
    app.run(host="0.0.0.0", port=port, debug=True)
