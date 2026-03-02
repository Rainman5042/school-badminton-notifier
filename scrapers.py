"""
爬蟲模組 - 針對不同學校網站結構實作不同的爬取策略
優先使用 RSS Feed，最簡單可靠
"""
import logging
import feedparser
import requests
from bs4 import BeautifulSoup
from typing import List, Dict
from urllib.parse import urljoin
from datetime import datetime, timedelta, timezone
import time

logger = logging.getLogger(__name__)

# 共用 headers，模擬瀏覽器行為避免被阻擋
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7",
}

REQUEST_TIMEOUT = 30  # 秒


def fetch_announcements(school: Dict) -> List[Dict]:
    """
    根據學校設定，自動選擇對應的爬取策略。
    回傳統一格式的公告列表: [{"title": str, "url": str, "school": str}, ...]
    """
    scraper_type = school.get("type", "rss")
    try:
        if scraper_type == "rss":
            return _scrape_rss(school)
        elif scraper_type == "ischool":
            return _scrape_ischool(school)
        else:
            logger.warning(f"未知的爬取類型: {scraper_type}，學校: {school['name']}")
            return []
    except Exception as e:
        logger.error(f"爬取 {school['name']} 失敗: {e}", exc_info=True)
        return []


def _scrape_rss(school: Dict) -> List[Dict]:
    """
    RSS Feed 爬取 - 最簡單可靠的方式
    適用：中山國中、玉成國小（NSS 系統也有 RSS）
    """
    logger.info(f"正在透過 RSS 爬取: {school['name']}")

    feed = feedparser.parse(school["url"], agent=HEADERS["User-Agent"])

    announcements = []
    for entry in feed.entries:
        title = entry.get("title", "").strip()
        link = entry.get("link", "").strip()

        # 嘗試解析日期
        date_str = ""
        date_parsed = None
        for date_field in ("published_parsed", "updated_parsed"):
            tp = entry.get(date_field)
            if tp:
                try:
                    date_parsed = datetime(*tp[:6], tzinfo=timezone.utc)
                    date_str = date_parsed.strftime("%Y-%m-%d")
                except Exception:
                    pass
                break

        # 如果 struct_time 解析失敗，嘗試字串欄位
        if not date_str:
            for raw_field in ("published", "updated"):
                raw = entry.get(raw_field, "")
                if raw:
                    date_str = raw[:10]  # 取前 10 字元作為日期近似值
                    break

        if title:
            announcements.append({
                "title": title,
                "url": link,
                "school": school["name"],
                "date": date_str,
                "date_parsed": date_parsed,
            })

    logger.info(f"  從 {school['name']} RSS 取得 {len(announcements)} 則公告")
    return announcements


def _scrape_ischool(school: Dict) -> List[Dict]:
    """
    育成高中 - iSchool 系統爬取
    iSchool 的公告是 JS 動態載入，需透過內部 JSON API 取得。
    若 API 需要登入，則 fallback 到 HTML 解析（可能取得較少資料）。
    """
    logger.info(f"正在透過 iSchool 爬取: {school['name']}")
    announcements = []

    widget_url = school.get("news_widget_url", "")
    if not widget_url:
        logger.warning(f"  {school['name']} 沒有設定 news_widget_url")
        return announcements

    # 方法 1: 嘗試 iSchool JSON API（news_query_json.php）
    try:
        json_url = widget_url.replace("main2.php", "news_query_json.php")
        # 從 widget URL 擷取 uid 參數
        import re
        uid_match = re.search(r'uid=([^&]+)', widget_url)
        uid = uid_match.group(1) if uid_match else ""

        if uid:
            api_resp = requests.post(
                json_url,
                headers={**HEADERS, "X-Requested-With": "XMLHttpRequest"},
                data={"uid": uid, "maximize": "1", "page": "0"},
                timeout=REQUEST_TIMEOUT,
            )
            if api_resp.status_code == 200:
                content_type = api_resp.headers.get("content-type", "")
                if "json" in content_type or api_resp.text.strip().startswith(("{", "[")):
                    import json
                    data = json.loads(api_resp.text)
                    items = data if isinstance(data, list) else data.get("data", data.get("news", []))
                    for item in items:
                        title = item.get("title", item.get("news_title", "")).strip()
                        news_id = item.get("newsId", item.get("news_id", ""))
                        link = f"https://mars.yucsh.tp.edu.tw/ischool/publish_page/0/?cid={news_id}" if news_id else school["url"]
                        if title:
                            announcements.append({
                                "title": title,
                                "url": link,
                                "school": school["name"],
                                "date": "",
                                "date_parsed": None,
                            })
                    if announcements:
                        logger.info(f"  從 {school['name']} JSON API 取得 {len(announcements)} 則公告")
                        return announcements
    except Exception as e:
        logger.debug(f"  iSchool JSON API 嘗試失敗: {e}")

    # 方法 2: Fallback - 解析 widget HTML 頁面
    try:
        resp = requests.get(widget_url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
        resp.encoding = school.get("encoding", "utf-8")

        if resp.status_code != 200:
            logger.warning(f"  iSchool 回應碼: {resp.status_code}")
            return announcements

        soup = BeautifulSoup(resp.text, "lxml")
        skip_texts = {"第一頁", "上一頁", "下一頁", "最後一頁", "全部", "暫停", ":::"}

        for tag in soup.select("a[href]"):
            title = tag.get_text(strip=True)
            href = tag.get("href", "")

            if (title
                    and len(title) > 4
                    and title not in skip_texts
                    and "javascript:" not in href):

                if href and not href.startswith("http"):
                    href = urljoin("https://mars.yucsh.tp.edu.tw", href)

                announcements.append({
                    "title": title,
                    "url": href or school["url"],
                    "school": school["name"],
                    "date": "",
                    "date_parsed": None,
                })

    except Exception as e:
        logger.error(f"  iSchool HTML 爬取失敗: {e}")

    if not announcements:
        logger.warning(
            f"  ⚠️  {school['name']} 公告為 JS 動態載入，"
            f"靜態爬取無法取得。如需支援，請提供該校的 RSS URL。"
        )

    logger.info(f"  從 {school['name']} iSchool 取得 {len(announcements)} 則公告")
    return announcements


def filter_by_date(announcements: List[Dict], max_age_days: int = 30) -> List[Dict]:
    """
    過濾公告：只保留指定天數內的公告。
    若公告沒有日期資訊，則保留（寧可多顯示也不錯過）。
    """
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(days=max_age_days)
    filtered = []

    for ann in announcements:
        dp = ann.get("date_parsed")
        if dp is not None:
            if dp >= cutoff:
                filtered.append(ann)
            else:
                logger.debug(
                    f"  ⏳ 已過期（{ann.get('date', '')}）: {ann.get('title', '')}"
                )
        else:
            # 沒有結構化日期，嘗試從 date 字串解析
            date_str = ann.get("date", "")
            if date_str:
                try:
                    parsed = datetime.strptime(date_str[:10], "%Y-%m-%d").replace(
                        tzinfo=timezone.utc
                    )
                    if parsed >= cutoff:
                        filtered.append(ann)
                    else:
                        logger.debug(
                            f"  ⏳ 已過期（{date_str}）: {ann.get('title', '')}"
                        )
                    continue
                except ValueError:
                    pass
            # 無法判斷日期，預設保留
            filtered.append(ann)

    logger.info(
        f"📅 日期過濾：{len(announcements)} → {len(filtered)} 則"
        f"（過濾 {max_age_days} 天前的公告）"
    )
    return filtered


def filter_by_keywords(announcements: List[Dict], keywords: List[str]) -> List[Dict]:
    """
    過濾公告：只保留標題中包含指定關鍵字的公告
    """
    matched = []
    for ann in announcements:
        title = ann.get("title", "")
        matched_keywords = [kw for kw in keywords if kw in title]
        if matched_keywords:
            ann["matched_keywords"] = matched_keywords
            matched.append(ann)
            logger.info(f"  🎯 命中關鍵字 {matched_keywords}: {title}")

    return matched
