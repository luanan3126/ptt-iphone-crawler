import os
import requests
from bs4 import BeautifulSoup

# 從 GitHub Secrets 讀取密碼
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
HISTORY_FILE = "notified.txt"

def send_telegram_msg(text):
    """發送 Telegram 推播訊息"""
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": text,
        "disable_web_page_preview": False
    }
    try:
        res = requests.post(url, data=payload)
        print("Telegram 回應狀態:", res.status_code)
    except Exception as e:
        print(f"發送 Telegram 訊息失敗: {e}")

def load_history():
    """讀取已通知過的文章網址，避免重複發送"""
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return set(line.strip() for line in f if line.strip())
    return set()

def save_history(history):
    """將更新後的歷史網址寫回檔案"""
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        for url in sorted(history):
            f.write(f"{url}\n")

def check_ptt():
    # 搜尋 PTT MobileSales 版標題含「賣」的文章
    url = "https://www.ptt.cc/bbs/MobileSales/search?q=%E8%B3%A3"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    cookies = {"over18": "1"}

    notified_urls = load_history()
    new_notified_urls = set(notified_urls)

    try:
        res = requests.get(url, headers=headers, cookies=cookies)
        soup = BeautifulSoup(res.text, "html.parser")
        articles = soup.find_all("div", class_="r-ent")

        for article in articles:
            title_div = article.find("div", class_="title")
            if not title_div or not title_div.a:
                continue

            title = title_div.a.text.strip()
            article_url = "https://www.ptt.cc" + title_div.a["href"]
            title_lower = title.lower()

            # 基本排除條件：排除已售出、徵/買文章
            if "售出" in title_lower or "[徵" in title_lower or "[買" in title_lower:
                continue

            # 定義 3 種你要的目標組合 (都必須包含「賣」)
            cond1 = ("iphone" in title_lower) and ("13" in title_lower) and ("pro" in title_lower)
            cond2 = ("iphone" in title_lower) and ("15" in title_lower) and ("pro" in title_lower)
            cond3 = ("ipad" in title_lower)

            # 只要符合其中一種組合 (Condition 1 OR Condition 2 OR Condition 3)
            if cond1 or cond2 or cond3:
                # 檢查是否發送過
                if article_url not in notified_urls:
                    msg = f"🚨 PTT MobileSales 發現目標售出貼文！\n\n標題：{title}\n連結：{article_url}"
                    send_telegram_msg(msg)
                    new_notified_urls.add(article_url)
                    print(f"已發送推播: {title}")

        save_history(new_notified_urls)

    except Exception as e:
        print(f"爬取過程發生錯誤: {e}")

if __name__ == "__main__":
    check_ptt()
