# 🏸 學校羽球場地公告監控機器人

自動爬取指定台北市學校的最新公告，當公告標題中包含「場地」、「租用」、「羽球」等關鍵字時，自動發送 Discord 或 Email 通知。

## ✨ 功能特色

- 🔍 **自動爬取** - 支援多種學校網站系統（RSS、NSS、iSchool）
- 🏫 **多學校支援** - 目前監控三所台北市學校
- 🎯 **關鍵字過濾** - 可自由設定監控的關鍵字
- 💬 **Discord 通知** - 精美的 Embed 格式推送
- 📧 **Email 通知** - HTML 格式的美觀郵件
- ⏰ **定時排程** - 使用 GitHub Actions 每 30 分鐘自動檢查
- 💾 **去重機制** - 不會重複通知相同的公告
- 🆓 **完全免費** - 使用 GitHub Actions 免費額度運行

## 🏫 監控學校

| 學校 | 網站系統 | 爬取方式 |
|------|----------|----------|
| 台北市中山國中 | 傳統 ASP | RSS Feed |
| 台北市玉成國小 | NSS 系統 | Web API + HTML Fallback |
| 台北市育成高中 | iSchool | Widget 頁面爬取 |

## 🚀 快速開始

### 1️⃣ Fork 此 Repo

點擊右上角的 **Fork** 按鈕。

### 2️⃣ 設定 Discord Webhook

1. 到你的 Discord 頻道 → **設定** → **整合** → **Webhook**
2. 點擊 **新增 Webhook**，複製 Webhook URL
3. 到你 Fork 的 GitHub Repo → **Settings** → **Secrets and variables** → **Actions**
4. 新增 Secret：
   - Name: `DISCORD_WEBHOOK_URL`
   - Value: 你的 Webhook URL

### 3️⃣ （可選）設定 Email 通知

到 GitHub Repo **Settings** → **Secrets and variables** → **Actions**，新增以下 Secrets：

| Secret 名稱 | 說明 |
|-------------|------|
| `EMAIL_ENABLED` | `true` |
| `SMTP_SERVER` | `smtp.gmail.com` |
| `SMTP_PORT` | `587` |
| `EMAIL_SENDER` | 你的 Gmail 地址 |
| `EMAIL_PASSWORD` | Gmail 應用程式密碼（[如何取得？](https://support.google.com/accounts/answer/185833)） |
| `EMAIL_RECEIVER` | 接收通知的信箱 |

### 4️⃣ 自訂關鍵字（可選）

新增 Secret：
- Name: `KEYWORDS`
- Value: `場地,租用,羽球,羽毛球,球場,體育館租借,活動中心`

### 5️⃣ 啟用 GitHub Actions

到 Repo 的 **Actions** 頁面 → 點擊 **I understand my workflows, go ahead and enable them**

完成！機器人會每 30 分鐘自動檢查一次 🎉

## 🖥️ 本地開發

```bash
# 複製 repo
git clone https://github.com/YOUR_USERNAME/school-badminton-notifier.git
cd school-badminton-notifier

# 建立虛擬環境
python3 -m venv venv
source venv/bin/activate  # Linux/macOS
# venv\Scripts\activate   # Windows

# 安裝依賴
pip install -r requirements.txt

# 複製環境變數範本
cp .env.example .env
# 編輯 .env 填入你的設定

# 乾跑模式（只看結果不發送通知）
python main.py --dry-run

# 正式執行
python main.py

# 強制通知所有匹配公告（忽略已通知紀錄）
python main.py --force
```

## 📁 專案結構

```
school-badminton-notifier/
├── .github/
│   └── workflows/
│       └── check.yml          # GitHub Actions 排程設定
├── data/
│   └── notified.json          # 已通知紀錄（自動產生）
├── .env.example               # 環境變數範本
├── .gitignore
├── config.py                  # 組態設定
├── main.py                    # 主程式入口
├── scrapers.py                # 爬蟲模組（支援 RSS/API/HTML）
├── notifier.py                # 通知模組（Discord/Email）
├── storage.py                 # 去重紀錄儲存模組
├── requirements.txt           # Python 依賴
└── README.md
```

## ⚙️ 新增監控學校

編輯 `config.py` 中的 `SCHOOLS` 列表，新增一筆學校設定：

```python
{
    "name": "學校名稱",
    "type": "rss",         # 爬取類型: rss / web_api / ischool / web_html
    "url": "https://...",  # 學校公告頁面 URL
    "encoding": "utf-8",   # 頁面編碼
}
```

支援的爬取類型：

| 類型 | 說明 | 適用場景 |
|------|------|----------|
| `rss` | RSS Feed | 有提供 RSS 的網站 |
| `web_api` | API 呼叫 | NSS 系統的學校（新北/台北校園網站） |
| `ischool` | iSchool Widget | 使用 iSchool 系統的學校 |
| `web_html` | 通用 HTML | 任何網頁（fallback） |

## 📊 GitHub Actions 免費額度

GitHub Actions 對公開 Repo **完全免費**，對私有 Repo 每月提供 **2,000 分鐘**的免費額度。

此機器人每次執行約 1-2 分鐘，每天 48 次 = 約 **48-96 分鐘/天**，一個月約 **1,440-2,880 分鐘**。

> 💡 **建議使用公開 Repo** 以享受無限免費額度，或調整 cron 為每小時一次（`0 * * * *`）以減少使用量。

## 🐛 常見問題

### Q: 為什麼沒有收到通知？
1. 確認 Discord Webhook URL 是否正確
2. 到 GitHub Actions 頁面查看執行結果和 log
3. 用 `--dry-run` 模式測試是否能爬到公告

### Q: 如何修改檢查頻率？
編輯 `.github/workflows/check.yml` 中的 cron 設定：
```yaml
schedule:
  - cron: '0 * * * *'    # 每小時
  - cron: '*/30 * * * *'  # 每 30 分鐘
  - cron: '*/15 * * * *'  # 每 15 分鐘
```

### Q: 學校網站改版了怎麼辦？
修改 `scrapers.py` 中對應學校的爬取邏輯，或在 GitHub 上建立 Issue。

## 📄 License

MIT License
