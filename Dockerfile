FROM python:3.11-slim

WORKDIR /app

# 安裝 tzdata 並將容器時區固定為台北時間（UTC+8），
# 讓程式中 datetime.now()（main.py 執行結果時間戳記、storage.py 通知紀錄時間戳記）正確反映在地時間
RUN apt-get update \
    && apt-get install -y --no-install-recommends tzdata \
    && rm -rf /var/lib/apt/lists/*
ENV TZ=Asia/Taipei

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# 無參數 -> 啟動常駐排程 + Web 手動觸發服務；有參數（如 --dry-run/--force）-> 一次性執行後結束
ENTRYPOINT ["python", "server.py"]
