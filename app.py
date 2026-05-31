import os
import requests
from flask import Flask, request

app = Flask(__name__)

VERIFY_TOKEN = os.environ.get("VERIFY_TOKEN", "mening_maxfiy_parolim_123")
PAGE_ACCESS_TOKEN = os.environ.get("PAGE_ACCESS_TOKEN", "")
# Render > Environment ga qo'shing (quyida avtomatik topish yo'li bor)
INSTAGRAM_ACCOUNT_ID = os.environ.get("INSTAGRAM_ACCOUNT_ID", "")

def get_instagram_account_id():
    """
    Avtomatik Instagram Business Account ID topish.
    Bir marta ishga tushganda aniqlanadi.
    """
    global INSTAGRAM_ACCOUNT_ID
    if INSTAGRAM_ACCOUNT_ID:
        return INSTAGRAM_ACCOUNT_ID

    if not PAGE_ACCESS_TOKEN:
        print("❌ PAGE_ACCESS_TOKEN yo'q!")
        return None

    # 1. Page ID olish
    r = requests.get(
        "https://graph.facebook.com/v21.0/me/accounts",
        params={"access_token": PAGE_ACCESS_TOKEN}
    )
    data = r.json()
    print("📋 Pages:", data)

    pages = data.get("data", [])
    if not pages:
        print("❌ Hech qanday Page topilmadi. Token Page Access Token emasmi?")
        return None

    page_id = pages[0]["id"]
    page_token = pages[0].get("access_token", PAGE_ACCESS_TOKEN)
    print(f"✅ Page ID: {page_id}")

    # 2. Instagram Business Account ID olish
    r2 = requests.get(
        f"https://graph.facebook.com/v21.0/{page_id}",
        params={
            "fields": "instagram_business_account",
            "access_token": page_token
        }
    )
    data2 = r2.json()
    print("📋 Instagram account:", data2)

    ig_account = data2.get("instagram_business_account", {})
    ig_id = ig_account.get("id")

    if ig_id:
        INSTAGRAM_ACCOUNT_ID = ig_id
        print(f"✅ Instagram Business Account ID: {ig_id}")
        print(f"👉 Render > Environment > INSTAGRAM_ACCOUNT_ID = {ig_id}  qilib saqlang!")
    else:
        print("❌ Instagram Business Account topilmadi.")
        print("   Instagram sahifangiz Facebook Page ga ulangan bo'lishi kerak!")

    return ig_id


@app.route('/', methods=['GET'])
def home():
    ig_id = INSTAGRAM_ACCOUNT_ID or get_instagram_account_id()
    token_ok = "✅ Bor" if PAGE_ACCESS_TOKEN else "❌ Yo'q"
    ig_ok = f"✅ {ig_id}" if ig_id else "❌ Topilmadi"
    return (
        f"<h2>Instagram Bot ✅ Ishlayapti</h2>"
        f"<p>🔑 Token: {token_ok}</p>"
        f"<p>📱 Instagram ID: {ig_ok}</p>"
    ), 200


@app.route('/webhook', methods=['GET'])
def verify_webhook():
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")
    if mode == "subscribe" and token == VERIFY_TOKEN:
        print("✅ Webhook tasdiqlandi!")
        return challenge, 200
    print(f"❌ Noto'g'ri token: {token}")
    return "Xato token", 403


@app.route('/webhook', methods=['POST'])
def receive_message():
    data = request.json
    print("📩 KELGAN DATA:", data)

    if data.get('object') == 'instagram':
        for entry in data.get('entry', []):

            # 1. JONLI DIRECT MESSAGES
            for event in entry.get('messaging', []):
                msg = event.get('message', {})
                if msg.get('is_echo'):
                    continue
                if 'text' in msg:
                    sender_id = event['sender']['id']
                    text = msg['text']
                    print(f"💬 DM keldi: {sender_id} → {text}")
                    send_dm(sender_id, "Assalomu alaykum! Xabaringizni oldik, tez orada javob beramiz 🙏")

            # 2. CHANGES (kommentlar, test xabarlar)
            for change in entry.get('changes', []):
                field = change.get('field')
                value = change.get('value', {})

                if field == 'messages':
                    msg = value.get('message', {})
                    if 'text' in msg:
                        sender_id = value.get('sender', {}).get('id', '')
                        print(f"📨 Changes DM: {msg['text']}")
                        # Test xabar (sender_id = '12334') bo'lsa yuborma
                        if sender_id and sender_id != '12334':
                            send_dm(sender_id, "Xabaringizni qabul qildik! ✅")
                        else:
                            print("ℹ️ Test xabar, yuborilmadi.")

                elif field == 'comments':
                    comment_id = value.get('id', '')
                    comment_text = value.get('text', '')
                    username = value.get('from', {}).get('username', 'foydalanuvchi')
                    print(f"💭 Komment: @{username}: {comment_text}")
                    if comment_id:
                        reply_to_comment(comment_id, "Rahmat! Savollar uchun DM yozing 📩")

    return "EVENT_RECEIVED", 200


def send_dm(recipient_id, text):
    """
    Instagram Direct Message yuborish.
    Instagram Business Account ID orqali.
    """
    if not PAGE_ACCESS_TOKEN:
        print("❌ TOKEN YO'Q!")
        return

    ig_id = INSTAGRAM_ACCOUNT_ID or get_instagram_account_id()
    if not ig_id:
        print("❌ INSTAGRAM_ACCOUNT_ID topilmadi, DM yuborib bo'lmaydi!")
        return

    url = f"https://graph.facebook.com/v21.0/{ig_id}/messages"
    payload = {
        "recipient": {"id": recipient_id},
        "message": {"text": text},
        "messaging_type": "RESPONSE",
        "access_token": PAGE_ACCESS_TOKEN
    }

    r = requests.post(url, json=payload)
    result = r.json()

    if r.status_code == 200:
        print(f"✅ DM yuborildi → {recipient_id}")
    else:
        err = result.get('error', {})
        print(f"❌ DM xato [{r.status_code}]: {err.get('message')}")
        if err.get('code') == 190:
            print("🔑 Token eskirgan! Render > Environment > PAGE_ACCESS_TOKEN yangilang.")


def reply_to_comment(comment_id, text):
    """Kommentga javob."""
    if not PAGE_ACCESS_TOKEN:
        print("❌ TOKEN YO'Q!")
        return

    url = f"https://graph.facebook.com/v21.0/{comment_id}/replies"
    payload = {
        "message": text,
        "access_token": PAGE_ACCESS_TOKEN
    }

    r = requests.post(url, json=payload)
    result = r.json()

    if r.status_code == 200:
        print(f"✅ Komment javobi yuborildi → {comment_id}")
    else:
        print(f"❌ Komment xato [{r.status_code}]: {result.get('error', {}).get('message')}")


# Server ishga tushganda ID ni oldindan aniqlash
if PAGE_ACCESS_TOKEN and not INSTAGRAM_ACCOUNT_ID:
    print("🔍 Instagram Account ID aniqlanmoqda...")
    get_instagram_account_id()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    print(f"🚀 Bot port {port} da ishga tushdi")
    app.run(host='0.0.0.0', port=port)
