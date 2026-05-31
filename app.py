import os
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

VERIFY_TOKEN = os.environ.get("VERIFY_TOKEN", "mening_maxfiy_parolim_123")
PAGE_ACCESS_TOKEN = os.environ.get("PAGE_ACCESS_TOKEN", "")
INSTAGRAM_ACCOUNT_ID = os.environ.get("INSTAGRAM_ACCOUNT_ID", "")

# ============================================================
# ASOSIY SAHIFALAR
# ============================================================

@app.route('/', methods=['GET'])
def home():
    token_ok = "✅ Bor" if PAGE_ACCESS_TOKEN else "❌ Yo'q"
    ig_ok = f"✅ {INSTAGRAM_ACCOUNT_ID}" if INSTAGRAM_ACCOUNT_ID else "❌ Yo'q"
    return (
        f"<h2>Instagram Bot ✅ Ishlayapti</h2>"
        f"<p>🔑 PAGE_ACCESS_TOKEN: {token_ok}</p>"
        f"<p>📱 INSTAGRAM_ACCOUNT_ID: {ig_ok}</p>"
        f"<hr>"
        f"<p>⚙️ Subscription o'rnatish: <a href='/setup'>/setup</a> sahifasini oching</p>"
        f"<p>🔍 Token tekshirish: <a href='/check'>/check</a> sahifasini oching</p>"
    ), 200


@app.route('/check', methods=['GET'])
def check():
    """Token va account ID ni tekshirish"""
    if not PAGE_ACCESS_TOKEN:
        return jsonify({"error": "PAGE_ACCESS_TOKEN yo'q! Render > Environment ga qo'shing."}), 400

    r = requests.get(
        "https://graph.facebook.com/v21.0/me",
        params={"access_token": PAGE_ACCESS_TOKEN, "fields": "id,name"}
    )
    me = r.json()

    r2 = requests.get(
        "https://graph.facebook.com/v21.0/me/accounts",
        params={"access_token": PAGE_ACCESS_TOKEN}
    )
    pages = r2.json()

    ig_info = None
    if INSTAGRAM_ACCOUNT_ID:
        r3 = requests.get(
            f"https://graph.facebook.com/v21.0/{INSTAGRAM_ACCOUNT_ID}",
            params={"access_token": PAGE_ACCESS_TOKEN, "fields": "id,name,username"}
        )
        ig_info = r3.json()

    return jsonify({
        "token_info": me,
        "pages": pages,
        "instagram_account": ig_info,
        "env": {
            "PAGE_ACCESS_TOKEN": "✅ Bor" if PAGE_ACCESS_TOKEN else "❌ Yo'q",
            "INSTAGRAM_ACCOUNT_ID": INSTAGRAM_ACCOUNT_ID or "❌ Yo'q"
        }
    })


@app.route('/setup', methods=['GET'])
def setup():
    """
    Instagram webhook subscription o'rnatish.
    Bir marta shu sahifani oching: https://sizning-bot.onrender.com/setup
    """
    if not PAGE_ACCESS_TOKEN:
        return jsonify({"error": "PAGE_ACCESS_TOKEN yo'q!"}), 400
    if not INSTAGRAM_ACCOUNT_ID:
        return jsonify({"error": "INSTAGRAM_ACCOUNT_ID yo'q! Render > Environment ga qo'shing."}), 400

    # Instagram account uchun app subscription
    url = f"https://graph.facebook.com/v21.0/{INSTAGRAM_ACCOUNT_ID}/subscribed_apps"
    r = requests.post(url, params={
        "access_token": PAGE_ACCESS_TOKEN,
        "subscribed_fields": "messages,comments,mentions,story_insights"
    })
    result = r.json()
    print("SETUP natijasi:", result)

    if result.get("success"):
        return jsonify({
            "status": "✅ Muvaffaqiyatli!",
            "message": "Webhook subscription o'rnatildi. Endi Instagram DM va kommentlarga javob beradi.",
            "result": result
        })
    else:
        return jsonify({
            "status": "❌ Xato",
            "result": result,
            "tavsiya": "Token Page Access Token bo'lishi kerak. /check sahifasini tekshiring."
        }), 400


# ============================================================
# WEBHOOK
# ============================================================

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

            # 2. CHANGES
            for change in entry.get('changes', []):
                field = change.get('field')
                value = change.get('value', {})

                if field == 'messages':
                    msg = value.get('message', {})
                    if 'text' in msg:
                        sender_id = value.get('sender', {}).get('id', '')
                        text = msg['text']
                        print(f"📨 Changes DM: sender={sender_id}, text={text}")
                        # Test xabar (Facebook test sender ID = '12334')
                        if sender_id and sender_id not in ('12334', '0'):
                            send_dm(sender_id, "Assalomu alaykum! Xabaringizni oldik 🙏")
                        else:
                            print("ℹ️ Test xabar, yuborilmadi.")

                elif field == 'comments':
                    comment_id = value.get('id', '')
                    comment_text = value.get('text', '')
                    username = value.get('from', {}).get('username', 'foydalanuvchi')
                    commenter_id = value.get('from', {}).get('id', '')
                    print(f"💭 Komment: @{username} ({commenter_id}): {comment_text}")
                    if comment_id:
                        reply_to_comment(comment_id, "Rahmat! Batafsil ma'lumot uchun DM yozing 📩")

    return "EVENT_RECEIVED", 200


# ============================================================
# YORDAMCHI FUNKSIYALAR
# ============================================================

def send_dm(recipient_id, text):
    """Instagram Direct Message yuborish"""
    if not PAGE_ACCESS_TOKEN:
        print("❌ PAGE_ACCESS_TOKEN yo'q!")
        return
    if not INSTAGRAM_ACCOUNT_ID:
        print("❌ INSTAGRAM_ACCOUNT_ID yo'q! Render > Environment ga qo'shing.")
        return

    url = f"https://graph.facebook.com/v21.0/{INSTAGRAM_ACCOUNT_ID}/messages"
    payload = {
        "recipient": {"id": recipient_id},
        "message": {"text": text},
        "messaging_type": "RESPONSE",
        "access_token": PAGE_ACCESS_TOKEN
    }

    r = requests.post(url, json=payload)
    result = r.json()

    if r.status_code == 200:
        print(f"✅ DM yuborildi → {recipient_id}: {text}")
    else:
        err = result.get('error', {})
        print(f"❌ DM xato [{r.status_code}]: code={err.get('code')} | {err.get('message')}")
        if err.get('code') == 190:
            print("🔑 Token eskirgan! Render > Environment > PAGE_ACCESS_TOKEN yangilang.")
        elif err.get('code') == 100:
            print("🔒 Permission xato. instagram_manage_messages ruxsati bormi?")


def reply_to_comment(comment_id, text):
    """Kommentga javob berish"""
    if not PAGE_ACCESS_TOKEN:
        print("❌ PAGE_ACCESS_TOKEN yo'q!")
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


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    print(f"🚀 Bot port {port} da ishga tushdi")
    print(f"🔑 Token: {'✅' if PAGE_ACCESS_TOKEN else '❌ YOQ!'}")
    print(f"📱 Instagram ID: {INSTAGRAM_ACCOUNT_ID or '❌ YOQ!'}")
    app.run(host='0.0.0.0', port=port)
