"""
通知模組 - 負責將匹配到的公告發送到 Discord 或 Email
"""
import json
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Dict

import requests

import config

logger = logging.getLogger(__name__)


def send_discord(announcements: List[Dict]) -> bool:
    """
    透過 Discord Webhook 發送通知
    """
    webhook_url = config.DISCORD_WEBHOOK_URL

    if not webhook_url or "YOUR_WEBHOOK" in webhook_url:
        logger.warning("Discord Webhook URL 未設定，跳過 Discord 通知")
        return False

    for ann in announcements:
        school = ann.get("school", "未知學校")
        title = ann.get("title", "無標題")
        url = ann.get("url", "")
        keywords = ann.get("matched_keywords", [])

        # 使用 Discord Embed 格式，更美觀
        embed = {
            "title": f"🏸 羽球場地相關公告",
            "description": f"**{title}**",
            "color": 0x00D4AA,  # 綠色
            "fields": [
                {
                    "name": "🏫 學校",
                    "value": school,
                    "inline": True,
                },
                {
                    "name": "🔑 命中關鍵字",
                    "value": ", ".join(keywords) if keywords else "N/A",
                    "inline": True,
                },
            ],
            "footer": {
                "text": "羽球場地公告監控機器人",
            },
        }

        if url:
            embed["url"] = url
            embed["fields"].append({
                "name": "🔗 連結",
                "value": f"[查看公告]({url})",
                "inline": False,
            })

        payload = {
            "username": "🏸 羽球場地通知",
            "embeds": [embed],
        }

        try:
            resp = requests.post(
                webhook_url,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=15,
            )

            if resp.status_code in (200, 204):
                logger.info(f"✅ Discord 通知已發送: {title[:50]}")
            else:
                logger.error(f"❌ Discord 發送失敗 (HTTP {resp.status_code}): {resp.text}")
                return False

        except Exception as e:
            logger.error(f"❌ Discord 發送錯誤: {e}")
            return False

    return True


def send_email(announcements: List[Dict]) -> bool:
    """
    透過 Email (Gmail SMTP) 發送通知
    """
    if not config.EMAIL_ENABLED:
        logger.debug("Email 通知未啟用")
        return False

    if not all([config.EMAIL_SENDER, config.EMAIL_PASSWORD, config.EMAIL_RECEIVER]):
        logger.warning("Email 設定不完整，跳過 Email 通知")
        return False

    # 組合所有公告成一封信
    html_parts = []
    for ann in announcements:
        school = ann.get("school", "未知學校")
        title = ann.get("title", "無標題")
        url = ann.get("url", "#")
        keywords = ann.get("matched_keywords", [])

        html_parts.append(f"""
        <div style="border-left: 4px solid #00D4AA; padding: 12px; margin: 12px 0; background: #f9f9f9; border-radius: 4px;">
            <h3 style="margin: 0 0 8px 0; color: #333;">🏸 {title}</h3>
            <p style="margin: 4px 0; color: #666;">🏫 學校：{school}</p>
            <p style="margin: 4px 0; color: #666;">🔑 命中關鍵字：{', '.join(keywords)}</p>
            <a href="{url}" style="color: #00D4AA; text-decoration: none;">📎 查看公告 →</a>
        </div>
        """)

    html_body = f"""
    <html>
    <body style="font-family: 'Microsoft JhengHei', Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <div style="background: linear-gradient(135deg, #00D4AA, #00B4D8); padding: 20px; border-radius: 8px 8px 0 0;">
            <h1 style="color: white; margin: 0; font-size: 20px;">🏸 羽球場地公告通知</h1>
            <p style="color: rgba(255,255,255,0.8); margin: 8px 0 0 0;">發現 {len(announcements)} 則符合條件的公告</p>
        </div>
        <div style="padding: 16px; border: 1px solid #eee; border-top: none; border-radius: 0 0 8px 8px;">
            {''.join(html_parts)}
            <p style="color: #999; font-size: 12px; margin-top: 20px; text-align: center;">
                此郵件由羽球場地公告監控機器人自動發送
            </p>
        </div>
    </body>
    </html>
    """

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"🏸 羽球場地公告通知 - 發現 {len(announcements)} 則新公告"
    msg["From"] = config.EMAIL_SENDER
    msg["To"] = config.EMAIL_RECEIVER

    # 純文字版本
    text_content = "\n".join([
        f"[{a['school']}] {a['title']} - {a.get('url', '')}"
        for a in announcements
    ])
    msg.attach(MIMEText(text_content, "plain", "utf-8"))
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    try:
        with smtplib.SMTP(config.SMTP_SERVER, config.SMTP_PORT) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(config.EMAIL_SENDER, config.EMAIL_PASSWORD)
            server.sendmail(config.EMAIL_SENDER, config.EMAIL_RECEIVER, msg.as_string())

        logger.info(f"✅ Email 通知已發送到 {config.EMAIL_RECEIVER}")
        return True

    except Exception as e:
        logger.error(f"❌ Email 發送失敗: {e}")
        return False


def notify_all(announcements: List[Dict]) -> Dict[str, bool]:
    """
    透過所有已啟用的管道發送通知
    """
    results = {}

    if announcements:
        results["discord"] = send_discord(announcements)
        results["email"] = send_email(announcements)
    else:
        logger.info("沒有需要通知的公告")

    return results
