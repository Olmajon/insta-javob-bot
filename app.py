import os
import requests
from flask import Flask, request

app = Flask(__name__)

# ✅ Tokenlar FAQAT environment variable dan olinadi (kodda yozilmaydi!)
VERIFY_TOKEN = os.environ.get("VERIFY_TOKEN", "mening_maxfiy_parolim_123")
PAGE_ACCESS_TOKEN = os.environ.get("PAGE_ACCESS_TOKEN", "")

@app.route('/', methods=['GET'])
def home():
    return "Instagram Bot serveri ishlayapti! ✅", 200

@app.route('/webhook', methods=['GET'])
def verify_webhook():
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        print("✅ Webhook muvaffaqiyatli tasdiqlandi!")
        return challenge, 200
    print(f"❌ Webhook token xato: {token}")
    return "Xato token", 403

@app.route('/webhook', methods=['POST'])
def receive_message():
    data = request.json
    print("📩 KELGAN DATA:", data)

    if data.get('object') == 'instagram':
        for entry in data.get('entry', []):

            # 1. JONLI XABARLAR (Direct Messages)
            for messaging_event in entry.get('messaging', []):
                if 'message' in messaging_event:
                    msg = messaging_event['message']
                    # Echo va delivery xabarlarni o'tkazib yuborish
                    if msg.get('is_echo') or 'delivery' in messaging_event:
                        continue
                    if 'text' in msg:
                        sender_id = messaging_event['sender']['id']
                        message_text = msg['text']
                        print(f"💬 JONLI XABAR: sender={sender_id}, text={message_text}")
                        reply_text = f"Assalomu alaykum! Xabaringizni oldik. Tez orada javob beramiz! 🙏"
                        send_dm(sender_id, reply_text)

            # 2. KOMMENTLAR VA BOSHQA O'ZGARISHLAR
            for change_event in entry.get('changes', []):
                field = change_event.get('field')
                value = change_event.get('value', {})

                # A) XABARLAR (test/webhook orqali kelgan)
                if field == 'messages':
                    msg = value.get('message', {})
                    if 'text' in msg:
                        sender_id = value.get('sender', {}).get('id', '')
                        message_text = msg['text']
                        print(f"📨 CHANGES XABARI: {message_text}")
                        if sender_id:
                            send_dm(sender_id, "Xabaringizni qabul qildik! ✅")

                # B) KOMMENTARIYALAR
                elif field == 'comments':
                    comment_id = value.get('id', '')
                    comment_text = value.get('text', '')
                    from_user = value.get('from', {}).get('username', 'foydalanuvchi')
                    print(f"💭 KOMMENTARIYA: @{from_user}: {comment_text}")
                    if comment_id:
                        reply_text = "Fikringiz uchun katta rahmat! Savollaringiz bo'lsa DM yozing 📩"
                        reply_to_comment(comment_id, reply_text)

    return "EVENT_RECEIVED", 200


def send_dm(recipient_id, text):
    """
    Instagram Direct Message yuborish.
    ✅ To'g'ri endpoint: graph.facebook.com (Page token bilan)
    """
    if not PAGE_ACCESS_TOKEN:
        print("❌ PAGE_ACCESS_TOKEN topilmadi! Render > Environment ga token kiriting.")
        return

    # Instagram Connected to Facebook Page bo'lsa shu endpoint ishlatiladi:
    url = f"https://graph.facebook.com/v21.0/me/messages"
    
    headers = {"Content-Type": "application/json"}
    params = {"access_token": PAGE_ACCESS_TOKEN}
    payload = {
        "recipient": {"id": recipient_id},
        "message": {"text": text},
        "messaging_type": "RESPONSE"
    }
    
    response = requests.post(url, params=params, headers=headers, json=payload)
    result = response.json()
    
    if response.status_code == 200:
        print(f"✅ DM yuborildi: {result}")
    else:
        print(f"❌ DM xatosi (status {response.status_code}): {result}")
        # Token muammosi bo'lsa batafsil log
        if result.get('error', {}).get('code') == 190:
            print("🔑 TOKEN MUAMMOSI: Render > Environment > PAGE_ACCESS_TOKEN ni yangilang!")


def reply_to_comment(comment_id, text):
    """
    Instagram kommentga javob berish.
    ✅ To'g'ri endpoint: graph.facebook.com
    """
    if not PAGE_ACCESS_TOKEN:
        print("❌ PAGE_ACCESS_TOKEN topilmadi!")
        return

    url = f"https://graph.facebook.com/v21.0/{comment_id}/replies"
    
    headers = {"Content-Type": "application/json"}
    params = {"access_token": PAGE_ACCESS_TOKEN}
    payload = {"message": text}
    
    response = requests.post(url, params=params, headers=headers, json=payload)
    result = response.json()
    
    if response.status_code == 200:
        print(f"✅ Komment javobi yuborildi: {result}")
    else:
        print(f"❌ Komment xatosi (status {response.status_code}): {result}")


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    print(f"🚀 Bot {port}-portda ishga tushmoqda...")
    print(f"🔑 Token mavjud: {'✅ Ha' if PAGE_ACCESS_TOKEN else '❌ Yo`q - Environment Variable qo`shing!'}")
    app.run(host='0.0.0.0', port=port)
