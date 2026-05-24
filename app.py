import os
import requests
from flask import Flask, request

app = Flask(__name__)

VERIFY_TOKEN = "mening_maxfiy_parolim_123"
# O'zingiz olgan uzun tokenni pastdagi qo'shtirnoq ichiga joylang:
PAGE_ACCESS_TOKEN = "IGAAdHTWj0GMhBZAFlnUE9KYUFKQkVTQmpDZAGZAockNzMzZAtbE1FSXY5VGtWamx6NTNfWHR4dEk0TWdnX2pJczVIU3RLWmEtajBwWS1MTFBXdXZAuUXlqeW9FeER4UVQ2cElnTDhoMG1lcjllbG5QTXVaYWpfLU93ZAU5HOE1lXzdvSQZDZD"

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
    print("YANGI XABAR KELDI:", data)

    # Agar xabar Instagramdan kelgan bo'lsa
    if data.get('object') == 'instagram':
        for entry in data.get('entry', []):
            for messaging_event in entry.get('messaging', []):
                
                # Faqat boshqalar yozgan xabarga javob berish (bot o'ziga o'zi yozib 'loop' bo'lib qolmasligi uchun)
                if 'message' in messaging_event and 'is_echo' not in messaging_event['message']:
                    sender_id = messaging_event['sender']['id']
                    message_text = messaging_event['message'].get('text')
                    
                    if message_text:
                        # Mijozlarga yuboriladigan birlamchi avto-javob matni
                        reply_text = "Assalomu alaykum! Xabaringizni qabul qildik. Tez orada sizga javob beramiz."
                        send_message(sender_id, reply_text)

    return "EVENT_RECEIVED", 200

def send_message(recipient_id, text):
    # Meta'ning xabar yuborish API manzili
    url = f"https://graph.facebook.com/v19.0/me/messages"
    params = {"access_token": PAGE_ACCESS_TOKEN}
    headers = {"Content-Type": "application/json"}
    payload = {
        "recipient": {"id": recipient_id},
        "message": {"text": text}
    }
    
    # Xabarni yuborish
    response = requests.post(url, params=params, headers=headers, json=payload)
    print("JAVOB YUBORISH HOLATI:", response.text)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=10000)
