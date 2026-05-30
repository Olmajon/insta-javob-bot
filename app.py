import os
import requests
from flask import Flask, request

app = Flask(__name__)

VERIFY_TOKEN = "mening_maxfiy_parolim_123"
# O'zingiz olgan uzun tokenni pastdagi qo'shtirnoq ichiga joylang!
PAGE_ACCESS_TOKEN = "IGAAdHTWj0GMhBZAFpFYzJRNjVxNl9JWUdIYmp5SVhQRDlBZAzd3aTR4UUo3WnJ6aGdueENuQWFCTWMyZAlhCSUtRaV85ZAjViSGJBVWN4dU1TbFdyZAjVSZAnVIenV6ZAjlGVFRZAb1NEc25VVUtTWGs5RGJDSjZAVS2c2Y20yenAtR2NGSQZDZD"

@app.route('/', methods=['GET'])
def home():
    return "Bot serveri ishlayapti!", 200

@app.route('/webhook', methods=['GET'])
def verify_webhook():
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        print("WEBHOOK TASDIQLANDI!")
        return challenge, 200
    return "Xato token", 403

@app.route('/webhook', methods=['POST'])
def receive_message():
    data = request.json
    print("KELGAN DATA:", data)

    if data.get('object') == 'instagram':
        for entry in data.get('entry', []):
            
            # ==========================================
            # 1. DIRECT XABARLARNI USHBLASH (MESSAGING)
            # ==========================================
            for messaging_event in entry.get('messaging', []):
                # Faqat matni bor yangi xabarlarga javob berish
                if 'message' in messaging_event and 'text' in messaging_event['message']:
                    sender_id = messaging_event['sender']['id']
                    message_text = messaging_event['message']['text']
                    
                    # DIRECT UCHUN O'ZINGIZNING JAVOBINGIZNI SHU YERGA YOZING:
                    reply_text = f"Assalomu alaykum! '{message_text}' xabarini oldik. Tez orada javob beramiz!"
                    send_dm(sender_id, reply_text)

            # ==========================================
            # 2. KOMMENTARIYALARNI USHLASH (CHANGES)
            # ==========================================
            for change_event in entry.get('changes', []):
                if change_event.get('field') == 'comments':
                    value = change_event.get('value', {})
                    
                    # Agar haqiqatan ham komment kelgan bo'lsa
                    if value.get('item') == 'comment':
                        comment_id = value.get('id')
                        comment_text = value.get('text')
                        
                        # KOMMENT UCHUN O'ZINGIZNING JAVOBINGIZNI SHU YERGA YOZING:
                        reply_text = f"Fikringiz uchun rahmat! Sizga Direct orqali batafsil ma'lumot yuboramiz."
                        reply_to_comment(comment_id, reply_text)

    return "EVENT_RECEIVED", 200

def send_dm(recipient_id, text):
    """Directga xabar yuborish funksiyasi"""
    url = f"https://graph.facebook.com/v19.0/me/messages"
    params = {"access_token": PAGE_ACCESS_TOKEN}
    headers = {"Content-Type": "application/json"}
    payload = {
        "recipient": {"id": recipient_id},
        "message": {"text": text}
    }
    response = requests.post(url, params=params, headers=headers, json=payload)
    print("DIRECT JAVOB HOLATI:", response.text)

def reply_to_comment(comment_id, text):
    """Kommentariyaning tagiga (reply qilib) javob yozish funksiyasi"""
    url = f"https://graph.facebook.com/v19.0/{comment_id}/replies"
    params = {"access_token": PAGE_ACCESS_TOKEN}
    payload = {"message": text}
    response = requests.post(url, params=params, json=payload)
    print("KOMMENT JAVOB HOLATI:", response.text)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=10000)
