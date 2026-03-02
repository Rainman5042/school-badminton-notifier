"""
設定檔 - 學校公告爬蟲的所有組態都在這裡
"""
import os
from dotenv import load_dotenv

load_dotenv()

# ========== 關鍵字設定 ==========
DEFAULT_KEYWORDS = ["場地", "租用", "羽球", "羽毛球", "球場", "體育館租借", "活動中心"]
KEYWORDS = os.getenv("KEYWORDS", ",".join(DEFAULT_KEYWORDS)).split(",")
KEYWORDS = [k.strip() for k in KEYWORDS if k.strip()]

# ========== 學校來源設定 ==========
# 所有學校盡可能使用 RSS，最簡單可靠
SCHOOLS = [
    # --- RSS 類型（NSS 系統）---
    {
        "name": "台北市中山國中",
        "type": "rss",
        "url": "http://www.csjhs.tp.edu.tw/RSSFeed/RSS_news.asp?id={42D4F6E7-9BAD-4292-992E-3C1297385C52}",
    },
    {
        "name": "台北市玉成國小",
        "type": "rss",
        "url": "https://www.yhes.tp.edu.tw/nss/main/feeder/5a9759adef37531ea27bf1b0/Cq0o5XU2162?f=normal&vector=private&static=false",
    },
    {
        "name": "台北市三民國中",
        "type": "rss",
        "url": "https://www.smjh.tp.edu.tw/nss/main/feeder/5a9759adef37531ea27bf1b0/mFezR9R8508?f=normal&vector=private&static=false",
    },
    {
        "name": "台北市三民國小",
        "type": "rss",
        "url": "https://web.smps.tp.edu.tw/nss/main/feeder/5abf2d62aa93092cee58ceb4/yw8E5Nw3301?f=normal&%240=JjdVhOT8505&vector=private&static=false",
    },
    {
        "name": "台北市民權國小",
        "type": "rss",
        "url": "https://www.mqes.tp.edu.tw/nss/main/feeder/5a9759adef37531ea27bf1b0/wrneR3s7855?f=normal&vector=private&static=false",
    },
    {
        "name": "台北市民生國中",
        "type": "rss",
        "url": "https://www.msjh.tp.edu.tw/nss/main/feeder/5a9759adef37531ea27bf1b0/3KzOlKA0721?f=normal&vector=private&static=false",
    },
    {
        "name": "台北市潭美國小",
        "type": "rss",
        "url": "https://www.tmes.tp.edu.tw/nss/main/feeder/5a9759adef37531ea27bf1b0/fsBgcbc1809?f=normal&vector=private&static=false",
    },
    {
        "name": "台北市新湖國小",
        "type": "rss",
        "url": "https://www.shes.tp.edu.tw/nss/main/feeder/5abf2d62aa93092cee58ceb4/OtqYfPY1530242779495?f=normal&%240=e70d8fd590784def&vector=private&static=false",
    },
    {
        "name": "台北市興雅國小",
        "type": "rss",
        "url": "https://www.hyps.tp.edu.tw/nss/main/feeder/5abf2d62aa93092cee58ceb4/1534429046984?f=normal&%240=e0b9c738d1644c9c&vector=private&static=false",
    },
    {
        "name": "台北市成德國小",
        "type": "rss",
        "url": "https://www.ctps.tp.edu.tw/nss/main/feeder/5abf2d62aa93092cee58ceb4/150pFjE7175?f=normal&%240=Eeb0PdV0695&vector=private&static=false",
    },
    # --- RSS 類型（WordPress）---
    {
        "name": "台北市永吉國中",
        "type": "rss",
        "url": "https://www.yjjh.tp.edu.tw/feed/",
    },
    # --- HTML 爬取類型 ---
    {
        "name": "台北市南港高中",
        "type": "rpage",
        "url": "https://www.nksh.tp.edu.tw/p/403-1000-32-1.php",
        "link_pattern": "406-1000",
    },
    # --- iSchool 類型（JS 動態載入，效果有限）---
    {
        "name": "台北市育成高中",
        "type": "ischool",
        "url": "https://mars.yucsh.tp.edu.tw/home",
        "news_widget_url": "https://mars.yucsh.tp.edu.tw/ischool/widget/site_news/main2.php?uid=WID_0_2_4156d6f9e6b4050edebb5229a479ef67aceb848c&maximize=1&allbtn=0",
    },
    {
        "name": "台北市南港高工",
        "type": "ischool",
        "url": "https://www.nkhs.tp.edu.tw/home",
        "news_widget_url": "https://www.nkhs.tp.edu.tw/ischool/widget/site_news/main2.php?uid=WID_215_2_9124ddeac97ded32c4009358adac4f6a0dda4e8e&maximize=1&allbtn=0",
    },
]

# ========== Discord 設定 ==========
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL", "")

# ========== Email 設定 ==========
EMAIL_ENABLED = os.getenv("EMAIL_ENABLED", "false").lower() == "true"
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
EMAIL_SENDER = os.getenv("EMAIL_SENDER", "")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD", "")
EMAIL_RECEIVER = os.getenv("EMAIL_RECEIVER", "")

# ========== 資料存放 ==========
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
NOTIFIED_FILE = os.path.join(DATA_DIR, "notified.json")
