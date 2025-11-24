from flask import Flask, request, jsonify, render_template_string
import re

app = Flask(__name__)

# အီးမေးလ်များကို ယာယီမှတ်ထားမည့်နေရာ
emails_db = []

# Premium UI (HTML + Tailwind CSS + JavaScript)
HTML_PAGE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Buffalo Mail | Premium Temp Mail</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        body { background-color: #0f172a; color: #e2e8f0; font-family: 'Inter', sans-serif; }
        .glass-panel { background: rgba(30, 41, 59, 0.7); backdrop-filter: blur(10px); border: 1px solid rgba(255, 255, 255, 0.1); }
        .otp-code { background-color: #facc15; color: #000; padding: 2px 6px; border-radius: 4px; font-weight: bold; cursor: pointer; }
        .animate-pulse-slow { animation: pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite; }
    </style>
</head>
<body class="min-h-screen flex flex-col items-center justify-center p-4">

    <div class="w-full max-w-2xl glass-panel rounded-2xl shadow-2xl overflow-hidden p-6 relative">
        
        <div class="flex items-center justify-between mb-8 border-b border-gray-700 pb-4">
            <div class="flex items-center gap-3">
                <i class="fa-solid fa-shield-cat text-blue-500 text-3xl"></i>
                <div>
                    <h1 class="text-2xl font-bold text-white tracking-tight">Buffalo Admin</h1>
                    <p class="text-xs text-gray-400">Secure Temporary Inbox</p>
                </div>
            </div>
            <div class="flex items-center gap-2">
                <span class="w-2 h-2 rounded-full bg-green-500 animate-pulse"></span>
                <span class="text-xs text-green-400 font-medium">Live System</span>
            </div>
        </div>

        <div class="bg-slate-800 rounded-xl p-4 mb-6 border border-slate-700">
            <label class="text-xs text-gray-400 uppercase font-semibold tracking-wider mb-2 block">Your Temporary Address</label>
            <div class="flex flex-col sm:flex-row gap-3">
                <div class="relative flex-grow">
                    <input type="text" id="current-email" readonly 
                        class="w-full bg-slate-900 text-blue-400 font-mono text-lg py-3 px-4 rounded-lg border border-slate-700 focus:outline-none focus:border-blue-500 transition-all text-center sm:text-left"
                        value="Loading...">
                    <button onclick="copyEmail()" class="absolute right-2 top-2 text-gray-400 hover:text-white p-2 rounded-md hover:bg-slate-700 transition-colors">
                        <i class="fa-regular fa-copy"></i>
                    </button>
                </div>
                <button onclick="generateNewEmail()" class="bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded-lg font-medium transition-all shadow-lg hover:shadow-blue-500/20 flex items-center justify-center gap-2">
                    <i class="fa-solid fa-arrows-rotate"></i> New ID
                </button>
            </div>
        </div>

        <div class="space-y-4">
            <div class="flex justify-between items-center px-2">
                <h2 class="text-lg font-semibold text-white">Inbox</h2>
                <button onclick="fetchEmails()" class="text-sm text-blue-400 hover:text-blue-300 transition-colors flex items-center gap-2">
                    <i class="fa-solid fa-rotate-right" id="refresh-icon"></i> Refresh
                </button>
            </div>

            <div id="inbox" class="space-y-3 min-h-[200px]">
                <div class="text-center py-10 text-gray-500">
                    <i class="fa-solid fa-inbox text-4xl mb-3 opacity-50"></i>
                    <p>Waiting for incoming emails...</p>
                </div>
            </div>
        </div>

        <div class="mt-8 text-center text-xs text-gray-500">
            Powered by Cloudflare Workers & Python Flask
        </div>
    </div>

    <div id="toast" class="fixed bottom-5 right-5 bg-green-600 text-white px-6 py-3 rounded-lg shadow-xl transform translate-y-20 opacity-0 transition-all duration-300 z-50 flex items-center gap-3">
        <i class="fa-solid fa-circle-check"></i>
        <span id="toast-msg">Copied!</span>
    </div>

    <script>
        const DOMAIN = "buffaloadmin.online"; // Your Domain
        let myEmail = localStorage.getItem("saved_email_v2");

        // 1. Generate Email
        function generateNewEmail() {
            const randomStr = Math.random().toString(36).substring(7);
            myEmail = randomStr + "@" + DOMAIN;
            localStorage.setItem("saved_email_v2", myEmail);
            updateDisplay();
            document.getElementById("inbox").innerHTML = `
                <div class="text-center py-10 text-gray-500">
                    <i class="fa-solid fa-inbox text-4xl mb-3 opacity-50"></i>
                    <p>Inbox cleared. Waiting for new emails...</p>
                </div>`;
            showToast("New address generated!");
        }

        function updateDisplay() {
            if (!myEmail) generateNewEmail();
            document.getElementById("current-email").value = myEmail;
        }

        // 2. Copy to Clipboard
        function copyEmail() {
            const copyText = document.getElementById("current-email");
            copyText.select();
            copyText.setSelectionRange(0, 99999);
            navigator.clipboard.writeText(copyText.value);
            showToast("Email address copied!");
        }

        // 3. Show Toast Notification
        function showToast(msg) {
            const toast = document.getElementById("toast");
            document.getElementById("toast-msg").innerText = msg;
            toast.classList.remove("translate-y-20", "opacity-0");
            setTimeout(() => {
                toast.classList.add("translate-y-20", "opacity-0");
            }, 3000);
        }

        // 4. Fetch Emails & Parse Content
        async function fetchEmails() {
            if (!myEmail) return;
            
            const refreshIcon = document.getElementById("refresh-icon");
            refreshIcon.classList.add("fa-spin");

            try {
                const res = await fetch(`/api/emails?address=${myEmail}`);
                const data = await res.json();
                
                const inboxDiv = document.getElementById("inbox");

                if (data.length > 0) {
                    inboxDiv.innerHTML = data.reverse().map(msg => {
                        // Clean up the body text
                        let cleanBody = msg.body;
                        
                        // Try to extract useful text if it's messy
                        // Simple cleanup: highlight numbers (OTP)
                        cleanBody = cleanBody.replace(/\\b\\d{4,8}\\b/g, (match) => {
                            return `<span class="otp-code">${match}</span>`;
                        });
                        
                        // Convert newlines to HTML breaks
                        cleanBody = cleanBody.replace(/\\n/g, "<br>");

                        return `
                        <div class="bg-slate-800 border border-slate-700 rounded-lg p-4 hover:border-blue-500 transition-colors shadow-sm">
                            <div class="flex justify-between items-start mb-2">
                                <div class="font-bold text-white text-sm">${msg.sender}</div>
                                <span class="text-xs text-gray-500 bg-slate-900 px-2 py-1 rounded">Just now</span>
                            </div>
                            <div class="text-blue-400 font-medium text-sm mb-3">${msg.subject}</div>
                            <div class="text-gray-300 text-sm bg-slate-900 p-3 rounded-md font-mono overflow-x-auto whitespace-pre-wrap border border-slate-800">
                                ${cleanBody}
                            </div>
                        </div>
                        `;
                    }).join("");
                }
            } catch (e) { console.error(e); }
            
            setTimeout(() => refreshIcon.classList.remove("fa-spin"), 500);
        }

        // Initialize
        updateDisplay();
        setInterval(fetchEmails, 3000); // Check every 3 seconds
    </script>
</body>
</html>
"""

@app.route('/')
def home():
    return render_template_string(HTML_PAGE)

@app.route('/api/webhook', methods=['POST'])
def webhook():
    data = request.json
    if data:
        emails_db.append(data)
        if len(emails_db) > 100: emails_db.pop(0)
    return jsonify({"status": "received"}), 200

@app.route('/api/emails')
def get_emails():
    target = request.args.get('address')
    my_msgs = [m for m in emails_db if m.get('recipient') == target]
    return jsonify(my_msgs)

if __name__ == '__main__':
    app.run()
