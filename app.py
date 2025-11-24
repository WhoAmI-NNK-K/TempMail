from flask import Flask, request, jsonify, render_template_string
import random
import string

app = Flask(__name__)

# အီးမေးလ်များကို ယာယီမှတ်ထားမည့်နေရာ
emails_db = []

# Web Interface (HTML/CSS/JS)
HTML_PAGE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Unlimited Temp Mail</title>
    <style>
        body { font-family: 'Segoe UI', sans-serif; background: #f4f6f8; text-align: center; padding: 20px; }
        .container { max-width: 600px; margin: 0 auto; background: white; padding: 30px; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); }
        h2 { color: #333; }
        .email-box { background: #e3f2fd; color: #1565c0; padding: 15px; border-radius: 8px; font-size: 1.2em; font-weight: bold; margin: 20px 0; word-break: break-all; border: 2px dashed #90caf9; }
        .btn { background: #2196f3; color: white; border: none; padding: 10px 20px; border-radius: 5px; cursor: pointer; font-size: 16px; margin: 5px; }
        .btn:hover { background: #1976d2; }
        .btn-new { background: #4caf50; }
        .message-list { text-align: left; margin-top: 30px; }
        .msg-card { background: #fff; border: 1px solid #ddd; padding: 15px; margin-bottom: 10px; border-radius: 8px; border-left: 5px solid #2196f3; }
        .msg-meta { font-size: 0.9em; color: #666; margin-bottom: 5px; }
        .msg-body { background: #f9f9f9; padding: 10px; border-radius: 4px; margin-top: 10px; }
    </style>
</head>
<body>
    <div class="container">
        <h2>🚀 Temp Mail Generator</h2>
        <div id="current-email" class="email-box">Generating...</div>
        
        <button class="btn" onclick="fetchEmails()">🔄 Refresh Inbox</button>
        <button class="btn btn-new" onclick="generateNewEmail()">✨ New Address</button>

        <div id="inbox" class="message-list">
            <p style="text-align:center; color:#888">Waiting for emails...</p>
        </div>
    </div>

    <script>
        const DOMAIN = "buffaloadmin.online"; // အစ်ကို့ Domain နာမည်
        let myEmail = localStorage.getItem("saved_email");

        function generateNewEmail() {
            const randomStr = Math.random().toString(36).substring(7);
            myEmail = randomStr + "@" + DOMAIN;
            localStorage.setItem("saved_email", myEmail);
            updateDisplay();
            document.getElementById("inbox").innerHTML = '<p style="text-align:center; color:#888">Inbox cleared for new address.</p>';
        }

        function updateDisplay() {
            if (!myEmail) generateNewEmail();
            document.getElementById("current-email").innerText = myEmail;
        }

        async function fetchEmails() {
            if (!myEmail) return;
            const btn = document.querySelector(".btn");
            btn.innerText = "Checking...";
            
            try {
                const res = await fetch(`/api/emails?address=${myEmail}`);
                const data = await res.json();
                
                const inboxDiv = document.getElementById("inbox");
                if (data.length === 0) {
                    inboxDiv.innerHTML = '<p style="text-align:center; color:#888">No emails yet...</p>';
                } else {
                    inboxDiv.innerHTML = data.reverse().map(msg => `
                        <div class="msg-card">
                            <div class="msg-meta"><strong>From:</strong> ${msg.sender}</div>
                            <div class="msg-meta"><strong>Subject:</strong> ${msg.subject}</div>
                            <div class="msg-body">${msg.body}</div>
                        </div>
                    `).join("");
                }
            } catch (e) { console.error(e); }
            btn.innerText = "🔄 Refresh Inbox";
        }

        updateDisplay();
        setInterval(fetchEmails, 5000); // 5 စက္ကန့်တစ်ခါ အလိုအလျောက် စစ်မယ်
    </script>
</body>
</html>
"""

@app.route('/')
def home():
    return render_template_string(HTML_PAGE)

# Cloudflare မှ Data လက်ခံမည့်လမ်းကြောင်း
@app.route('/api/webhook', methods=['POST'])
def webhook():
    data = request.json
    if data:
        emails_db.append(data)
        # Memory များမသွားအောင် အစောင် ၁၀၀ ကျော်ရင် အဟောင်းတွေဖျက်မယ်
        if len(emails_db) > 100:
            emails_db.pop(0)
    return jsonify({"status": "received"}), 200

# Frontend သို့ Data ပြန်ပေးမည့်လမ်းကြောင်း
@app.route('/api/emails')
def get_emails():
    target = request.args.get('address')
    my_msgs = [m for m in emails_db if m.get('recipient') == target]
    return jsonify(my_msgs)

if __name__ == '__main__':
    app.run()
