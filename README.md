# 🏸 學校羽球場地公告監控機器人

自動爬取指定台北市學校的最新公告，當公告標題中包含「場地」、「租用」、「羽球」等關鍵字時，自動發送 Discord、Email 或 Teams 通知。

## ✨ 功能特色

- 🔍 **自動爬取** - 支援多種學校網站系統（RSS、NSS、iSchool）
- 🏫 **多學校支援** - 目前監控三所台北市學校
- 🎯 **關鍵字過濾** - 可自由設定監控的關鍵字
- 💬 **Discord 通知** - 精美的 Embed 格式推送
- 📧 **Email 通知** - HTML 格式的美觀郵件
- 👥 **Teams 通知** - 透過 Power Automate Workflows Webhook 推送 Adaptive Card，多則公告會彙整成一張卡片，不洗版
- ⏰ **定時排程** - 容器內建排程（APScheduler），週一至週五台北時間 12:00 自動執行一次（詳見「Docker 常駐服務部署」）
- 💾 **去重機制** - 不會重複通知相同的公告

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

### 3️⃣ （可選）設定 Teams Webhook

微軟已於 2025 年底前逐步淘汰舊版 Office 365 Connector（Teams 頻道內建的 Incoming Webhook），目前建立 Teams webhook 的官方作法是透過 **Power Automate**：

1. 到 [Power Automate](https://make.powerautomate.com/) 建立一個新的雲端流程
2. 觸發器選擇 **「When a Teams webhook request is received」**
3. 動作選擇 **「Post card in a chat or channel」**，選擇要發送到的頻道，Adaptive Card 內容留給程式送入
4. 儲存後，複製觸發器產生的 HTTP POST URL
5. 設定環境變數 `TEAMS_WEBHOOK_URL`（本地 `.env`，或 GitHub Repo 的 Secret，用於 `workflow_dispatch` 手動測試）

> ⚠️ **常見錯誤**：若「Post card in a chat or channel」動作失敗並顯示 `Call made for a thread which is not a ChatThread`，代表「張貼於 (Post in)」設定的目標 ID 不是有效的 Chat 資源（常見於誤用頻道 ID 當作 Group chat ID）。最保險的排查/測試方式是把「張貼於」改成 **「與 Flow bot 聊天 (Chat with Flow bot)」**，「收件者 (Recipient)」直接填自己的 email，完全不需要任何 ID；正式要發頻道時，「張貼於」選 **「頻道 (Channel)」**，用下拉選單選 Team/Channel，不要手動貼 ID。

建好 webhook 後，可以用下面這支腳本快速驗證（繞過爬蟲/關鍵字比對，直接送出測試卡片，且一次送三筆測試資料驗證多筆彙整成一張卡片的效果）：

```bash
docker compose run --rm --entrypoint python notifier test_teams_webhook.py
```

### 4️⃣ （可選）設定 Email 通知

到 GitHub Repo **Settings** → **Secrets and variables** → **Actions**，新增以下 Secrets：

| Secret 名稱 | 說明 |
|-------------|------|
| `EMAIL_ENABLED` | `true` |
| `SMTP_SERVER` | `smtp.gmail.com` |
| `SMTP_PORT` | `587` |
| `EMAIL_SENDER` | 你的 Gmail 地址 |
| `EMAIL_PASSWORD` | Gmail 應用程式密碼（[如何取得？](https://support.google.com/accounts/answer/185833)） |
| `EMAIL_RECEIVER` | 接收通知的信箱 |

### 5️⃣ 自訂關鍵字（可選）

新增 Secret：
- Name: `KEYWORDS`
- Value: `場地,租用,羽球,羽毛球,球場,體育館租借,活動中心`

### 6️⃣ 部署排程

排程執行已內建於容器中（詳見下方「🐳 Docker 常駐服務部署」），GitHub Actions 只保留 `workflow_dispatch` 供手動測試，不會自動排程執行。

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

## 🐳 Docker 常駐服務部署

容器啟動後會常駐執行：內建排程（週一至週五台北時間 12:00 自動檢查一次）+ 網頁手動觸發介面（http://localhost:5000）。容器時區已透過 Dockerfile 固定為 Asia/Taipei，與主機時區無關。`data/`（去重紀錄）以 volume 掛載，`.env` 內的密鑰不會寫進 image。

```bash
# 建立 .env（同「本地開發」章節）
cp .env.example .env

# 建置 image
docker compose build

# 啟動常駐服務（背景執行，關閉終端機也會持續運作）
docker compose up -d

# 查看即時 log
docker compose logs -f notifier

# 停止服務
docker compose down
```

啟動後開啟 http://localhost:5000，點擊「🔍 立即檢查」即可手動觸發一次檢查（網頁未設驗證機制，僅建議在信任的內網環境開放存取）。

若只想做一次性測試、不啟動常駐服務，仍可用舊有方式：

```bash
docker compose run --rm notifier --dry-run   # 乾跑模式
docker compose run --rm notifier --force     # 強制通知所有匹配公告
docker compose run --rm notifier             # 正式執行一次
```

## 📁 專案結構

```
school-badminton-notifier/
├── .github/
│   └── workflows/
│       └── check.yml          # GitHub Actions 設定（僅 workflow_dispatch 手動測試）
├── data/
│   └── notified.json          # 已通知紀錄（自動產生）
├── docs/
│   └── results.json           # GitHub Pages 儀表板資料（自動產生）
├── templates/
│   └── index.html             # 手動觸發網頁
├── Dockerfile                  # 容器化設定（含台北時區）
├── docker-compose.yml          # 常駐服務用 compose 設定
├── .dockerignore
├── .env.example               # 環境變數範本
├── .gitignore
├── config.py                  # 組態設定
├── server.py                  # 容器進入點：常駐排程+Web服務／一次性 CLI 模式
├── main.py                    # 核心流程：main.run() / CLI 入口
├── web.py                     # Flask 手動觸發介面（/api/check, /api/status）
├── scrapers.py                # 爬蟲模組（支援 RSS/API/HTML）
├── notifier.py                # 通知模組（Discord/Email/Teams）
├── storage.py                 # 去重紀錄儲存模組
├── test_teams_webhook.py      # Teams webhook 手動測試腳本
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

## 🐛 常見問題

### Q: 為什麼沒有收到通知？
1. 確認 Discord/Teams Webhook URL 是否正確
2. Teams 通知可以用 `docker compose run --rm --entrypoint python notifier test_teams_webhook.py` 單獨測試，繞過爬蟲/關鍵字比對；若 HTTP 回應成功但 Teams 沒收到卡片，要到 Power Automate 該 flow 的「執行歷程記錄 (Run history)」查看實際錯誤（HTTP 200/202 只代表觸發程序有收到，不保證後續動作成功）
3. 檢查容器 log：`docker compose logs -f notifier`，或手動用 `docker compose run --rm notifier` 查看即時輸出
4. 用 `--dry-run` 模式測試是否能爬到公告

### Q: 如何修改檢查頻率？
編輯 `server.py` 中 `CronTrigger(day_of_week="mon-fri", hour=12, minute=0, ...)` 的參數（例如改成每小時、或改變執行的星期），然後重新建置並重啟：
```bash
docker compose up -d --build
```

### Q: 學校網站改版了怎麼辦？
修改 `scrapers.py` 中對應學校的爬取邏輯，或在 GitHub 上建立 Issue。

## 📄 License

MIT License
