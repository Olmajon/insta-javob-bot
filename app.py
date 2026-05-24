from flask import Flask, request

app = Flask(__name__)

# Bu maxfiy parolni keyin Meta portaliga ham kiritamiz
VERIFY_TOKEN = "mening_maxfiy_parolim_123"

@app.route('/', methods=['GET'])
def home():
    return "Bot serveri ishlayapti!", 200

@app.route('/webhook', methods=['GET'])
def verify_webhook():
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    if mode and token:
        if mode == "subscribe" and token == VERIFY_TOKEN:
            print("WEBHOOK MUVAFFAQIYATLI TASDIQLANDI!")
            return challenge, 200
        else:
            return "Xato token", 403
    return "Webhook ishlashga tayyor", 200

@app.route('/webhook', methods=['POST'])
def receive_message():
    data = request.json
    print("YANGI XABAR KELDI:", data)
    return "EVENT_RECEIVED", 200

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=10000)
