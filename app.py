import os
import requests
from flask import Flask, request

app = Flask(__name__)

VERIFY_TOKEN = "mening_maxfiy_parolim_123"
# O'zingizning uzooon oltin kalitingizni (Token) pastdagi qo'shtirnoq ichiga aniq joylang!
PAGE_ACCESS_TOKEN = "IGAAdHTWj0GMhBZAGFacmpMS2J4eHhmTWtySU9JMUlfc20zOXFiTjROTGhTcTdaUlozYm1GVTNIenpDSWNRY3FtbmVRWkttSlduRm0wY2E3dWVzWW12SG9Pa0d3UVJvTjVXQnNJREQ4RjhTQWFZAMXE2U2Y4REtqNXVRS0lmTWxQcwZDZD"

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
            # 1. JONLI REJIM: MESSAGING ICHIDAN QIDIRISH
            # ==========================================
            for messaging_event in entry.get('messaging', []):
                if 'message' in messaging_event and 'text' in messaging_event['message']:
                    sender_id = messaging_event['sender']['id']
                    message_text = messaging_event['message']['text']
                    
                    print(f"JONLI XABAR KELDI: {message_text}")
                    reply_text = f"Assalomu alaykum! '{message_text}' xabarini oldik. Tez orada javob beramiz!"
                    send_dm(sender_id, reply_text)

            # ==========================================
            # 2. SINOV REJIMI VA KOMMENTLAR: CHANGES ICHIDAN QIDIRISH
            # ==========================================
            for change_event in entry.get('changes', []):
                field = change_event.get('field')
                value = change_event.get('value', {})
                
                # A) Agar TEST rejimida xabar (messages) kelsa
                if field == 'messages':
                    if 'message' in value and 'text' in value['message']:
                        sender_id = value.get('sender', {}).get('id', '12334')
                        message_text = value['message']['text']
                        
                        print(f"TEST XABARI KELDI: {message_text}")
                        reply_text = f"Test xabari muvaffaqiyatli qabul qilindi! Kod ishlayapti."
                        send_dm(sender_id, reply_text)
                
                # B) Agar KOMMENTARIYA (comments) kelsa
                elif field == 'comments':
                    if value.get('item') == 'comment' or 'text' in value:
                        comment_id = value.get('id', '17865799348089039')
                        comment_text = value.get('text', '')
                        
                        print(f"KOMMENTARIYA KELDI: {comment_text}")
                        reply_text = f"Fikringiz uchun rahmat! Sizga Direct orqali batafsil ma'lumot yuboramiz."
                        reply_to_comment(comment_id, reply_text)

    return "EVENT_RECEIVED", 200

def send_dm(recipient_id, text):
    """Directga xabar yuborish funksiyasi"""
    url = "https://graph.facebook.com/v19.0/me/messages"
    params = {"access_token": PAGE_ACCESS_TOKEN}
    headers = {"Content-Type": "application/json"}
    payload = {
        "recipient": {"id": recipient_id},
        "message": {"text": text}
    }
    response = requests.post(url, params=params, headers=headers, json=payload)
    print("DIRECT JAVOB HOLATI:", response.text)

def reply_to_comment(comment_id, text):
    """Kommentariyaning tagiga javob yozish funksiyasi"""
    url = f"https://graph.facebook.com/v19.0/{comment_id}/replies"
    params = {"access_token": PAGE_ACCESS_TOKEN}
    payload = {"message": text}
    response = requests.post(url, params=params, json=payload)
    print("KOMMENT JAVOB HOLATI:", response.text)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=10000)
