import os
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

VERIFY_TOKEN = os.environ.get("VERIFY_TOKEN", "mening_maxfiy_parolim_123")
ACCESS_TOKEN = os.environ.get("PAGE_ACCESS_TOKEN", "")
INSTAGRAM_ACCOUNT_ID = os.environ.get("INSTAGRAM_ACCOUNT_ID", "")

# ============================================================
# SAHIFALAR
# ============================================================

@app.route('/', methods=['GET'])
def home():
    token_ok = "✅ Bor" if ACCESS_TOKEN else "❌ Yo'q"
    ig_ok = f"✅ {INSTAGRAM_ACCOUNT_ID}" if INSTAGRAM_ACCOUNT_ID else "❌ Yo'q"
    return (
        f"<h2>Instagram Bot ✅ Ishlayapti</h2>"
        f"<p>🔑 ACCESS_TOKEN: {token_ok}</p>"
        f"<p>📱 INSTAGRAM_ACCOUNT_ID: {ig_ok}</p>"
        f"<hr>"
        f"<p>🔍 Token tekshirish: <a href='/check'>/check</a></p>"
        f"<p>⚙️ Subscription: <a href='/setup'>/setup</a></p>"
    ), 200


@app.route('/check', methods=['GET'])
def check():
    if not ACCESS_TOKEN:
        return jsonify({"xato": "ACCESS_TOKEN yo'q! Render > Environment ga qo'shing."}), 400

    # Yangi Instagram API bilan tekshirish
    r = requests.get(
        "https://graph.instagram.com/v25.0/me",
        params={"access_token": ACCESS_TOKEN, "fields": "id,name,username"}
    )
    return jsonify({
        "instagram_me": r.json(),
        "token": "✅ Bor" if ACCESS_TOKEN else "❌ Yo'q",
        "instagram_id": INSTAGRAM_ACCOUNT_ID or "❌ Yo'q"
    })


@app.route('/setup', methods=['GET'])
def setup():
    """Webhook subscription o'rnatish"""
    if not ACCESS_TOKEN:
        return jsonify({"xato": "ACCESS_TOKEN yo'q!"}), 400
    if not INSTAGRAM_ACCOUNT_ID:
        return jsonify({"xato": "INSTAGRAM_ACCOUNT_ID yo'q!"}), 400

    # Yangi Instagram API subscription
    url = f"https://graph.instagram.com/v25.0/{INSTAGRAM_ACCOUNT_ID}/subscribed_apps"
    r = requests.post(url, params={
        "access_token": ACCESS_TOKEN,
        "subscribed_fields": "messages,comments"
    })
    result = r.json()
    print("SETUP natijasi:", result)

    if result.get("success"):
        return jsonify({"holat": "✅ Muvaffaqiyatli! Bot tayyor."})
    else:
        return jsonify({"holat": "❌ Xato", "natija": result}), 400


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

            # 2. CHANGES (kommentlar)
            for change in entry.get('changes', []):
                field = change.get('field')
                value = change.get('value', {})

                if field == 'messages':
                    msg = value.get('message', {})
                    if 'text' in msg:
                        sender_id = value.get('sender', {}).get('id', '')
                        print(f"📨 Changes DM: sender={sender_id}")
                        if sender_id and sender_id not in ('12334', '0'):
                            send_dm(sender_id, "Assalomu alaykum! Xabaringizni oldik 🙏")
                        else:
                            print("ℹ️ Test xabar, yuborilmadi.")

                elif field == 'comments':
                    comment_id = value.get('id', '')
                    comment_text = value.get('text', '')
                    username = value.get('from', {}).get('username', '')
                    print(f"💭 Komment: @{username}: {comment_text}")
                    if comment_id:
                        reply_to_comment(comment_id, "Rahmat! Savollar uchun DM yozing 📩")

    return "EVENT_RECEIVED", 200


# ============================================================
# YORDAMCHI FUNKSIYALAR — YANGI Instagram API
# ============================================================

def send_dm(recipient_id, text):
    """
    Yangi Instagram API orqali DM yuborish
    graph.instagram.com/v25.0/me/messages
    """
    if not ACCESS_TOKEN:
        print("❌ ACCESS_TOKEN yo'q!")
        return

    url = "https://graph.instagram.com/v25.0/me/messages"
    payload = {
        "recipient": {"id": recipient_id},
        "message": {"text": text},
        "messaging_type": "RESPONSE",
        "access_token": ACCESS_TOKEN
    }

    r = requests.post(url, json=payload)
    result = r.json()

    if r.status_code == 200:
        print(f"✅ DM yuborildi → {recipient_id}")
    else:
        err = result.get('error', {})
        print(f"❌ DM xato [{r.status_code}]: {err.get('message')}")


def reply_to_comment(comment_id, text):
    """Kommentga javob"""
    if not ACCESS_TOKEN:
        print("❌ ACCESS_TOKEN yo'q!")
        return

    url = f"https://graph.instagram.com/v25.0/{comment_id}/replies"
    payload = {
        "message": text,
        "access_token": ACCESS_TOKEN
    }

    r = requests.post(url, json=payload)
    result = r.json()

    if r.status_code == 200:
        print(f"✅ Komment javobi yuborildi")
    else:
        print(f"❌ Komment xato [{r.status_code}]: {result.get('error', {}).get('message')}")


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    print(f"🚀 Bot port {port} da ishga tushdi")
    print(f"🔑 Token: {'✅' if ACCESS_TOKEN else '❌ YOQ!'}")
    app.run(host='0.0.0.0', port=port)
