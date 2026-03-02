#!/usr/bin/env python3
"""
主程式 - 學校羽球場地公告監控
從指定學校網站爬取最新公告，若包含羽球場地租用相關關鍵字，
自動透過 Discord / Email 發送通知。
"""
import sys
import logging
import argparse
from datetime import datetime

import config
from scrapers import fetch_announcements, filter_by_keywords, filter_by_date
from notifier import notify_all
from storage import filter_new_announcements, mark_as_notified

# ========== 日誌設定 ==========
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("main")


def run(dry_run: bool = False, force: bool = False) -> dict:
    """
    執行一次完整的爬取 → 過濾 → 通知流程
    
    Args:
        dry_run: 只爬取和過濾，不發送通知也不記錄
        force:   忽略已通知紀錄，強制通知所有匹配公告
    
    Returns:
        dict: 執行結果
    """
    result = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "keywords": config.KEYWORDS,
        "school_count": len(config.SCHOOLS),
        "total_fetched": 0,
        "after_date_filter": 0,
        "keyword_matched": 0,
        "new_announcements": [],
        "all_matched": [],
        "notify_results": {},
        "status": "success",
        "message": "",
        "dry_run": dry_run,
        "force": force,
    }

    logger.info("=" * 60)
    logger.info(f"🏸 羽球場地公告監控 - 開始執行")
    logger.info(f"   時間: {result['timestamp']}")
    logger.info(f"   關鍵字: {config.KEYWORDS}")
    logger.info(f"   監控學校數: {len(config.SCHOOLS)}")
    logger.info("=" * 60)

    # Step 1: 爬取所有學校的公告
    all_announcements = []
    for school in config.SCHOOLS:
        logger.info(f"\n--- 爬取: {school['name']} ---")
        announcements = fetch_announcements(school)
        all_announcements.extend(announcements)

    result["total_fetched"] = len(all_announcements)
    logger.info(f"\n📊 共爬取到 {len(all_announcements)} 則公告")

    if not all_announcements:
        logger.warning("⚠️  未取得任何公告，請檢查網路連線或學校網站是否正常")
        result["status"] = "warning"
        result["message"] = "未取得任何公告，請檢查網路連線或學校網站是否正常"
        return result

    # Step 2: 日期過濾（只保留一個月內的公告）
    all_announcements = filter_by_date(all_announcements, max_age_days=30)
    result["after_date_filter"] = len(all_announcements)

    if not all_announcements:
        logger.info("✅ 所有公告都已超過一個月，本次無有效公告")
        result["message"] = "所有公告都已超過一個月，本次無有效公告"
        return result

    # Step 3: 用關鍵字過濾
    matched = filter_by_keywords(all_announcements, config.KEYWORDS)
    result["keyword_matched"] = len(matched)
    result["all_matched"] = matched
    logger.info(f"🔍 關鍵字匹配: {len(matched)} 則")

    if not matched:
        logger.info("✅ 本次沒有匹配到羽球場地相關公告")
        result["message"] = "本次沒有匹配到羽球場地相關公告"
        return result

    # Step 4: 過濾已通知的（避免重複通知）
    if force:
        new_announcements = matched
        logger.info(f"⚡ 強制模式: 所有 {len(new_announcements)} 則匹配公告都會通知")
    else:
        new_announcements = filter_new_announcements(matched)

    result["new_announcements"] = new_announcements

    if not new_announcements:
        logger.info("✅ 所有匹配的公告都已通知過，本次無新公告")
        result["message"] = "所有匹配的公告都已通知過，本次無新公告"
        return result

    # Step 5: 發送通知
    logger.info(f"\n📢 準備發送 {len(new_announcements)} 則新公告通知")
    for ann in new_announcements:
        logger.info(f"  📌 [{ann['school']}] {ann['title']}")

    if dry_run:
        logger.info("\n🔍 [DRY RUN] 僅顯示結果，不發送通知也不記錄")
        result["message"] = "[DRY RUN] 僅顯示結果，不發送通知也不記錄"
        return result

    notify_results = notify_all(new_announcements)
    result["notify_results"] = notify_results

    # Step 6: 標記為已通知
    if any(notify_results.values()):
        mark_as_notified(new_announcements)
        logger.info("✅ 已更新通知紀錄")
        result["message"] = f"已發送 {len(new_announcements)} 則通知"
    else:
        logger.warning("⚠️  所有通知管道都失敗，不標記為已通知（下次重試）")
        result["status"] = "warning"
        result["message"] = "所有通知管道都失敗，不標記為已通知（下次重試）"

    logger.info("\n🏁 執行完成")
    return result


def main():
    parser = argparse.ArgumentParser(
        description="🏸 學校羽球場地公告監控機器人",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
範例:
  python main.py                  # 正常執行
  python main.py --dry-run        # 只看結果不發送通知
  python main.py --force          # 忽略歷史紀錄，強制通知所有匹配公告
  python main.py --dry-run --force  # 顯示所有匹配公告（含已通知過的）
        """,
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="乾跑模式：只爬取和過濾，不發送通知",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="強制模式：忽略已通知紀錄",
    )

    args = parser.parse_args()

    try:
        run(dry_run=args.dry_run, force=args.force)
    except KeyboardInterrupt:
        logger.info("\n⏹️  使用者中斷執行")
        sys.exit(0)
    except Exception as e:
        logger.error(f"💥 執行發生錯誤: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
