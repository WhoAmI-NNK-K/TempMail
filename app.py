from flask import Flask, request, jsonify, render_template_string
import re

app = Flask(__name__)

# Server Memory (Temporary Storage)
# Server Restart ကျရင် စာအဟောင်းတွေ ပျောက်သွားနိုင်ပေမယ့်
# Email လိပ်စာအဟောင်းကို ပြန်သုံးပြီး စာအသစ်လက်ခံလို့ ရပါတယ်
emails_db = []

HTML_PAGE = """
<!DOCTYPE html>
<html lang="en" class="dark"> <head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Buffalo Admin | Premium Mail</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script>
        tailwind.config = {
            darkMode: 'class',
            theme: {
                extend: {
                    colors: {
                        dark: { bg: '#0f172a', card: '#1e293b', text: '#f1f5f9' },
                        light: { bg: '#f3f4f6', card: '#ffffff', text: '#111827' }
                    }
                }
            }
        }
    </script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        body { transition: background-color 0.3s, color 0.3s; }
        .glass-panel { backdrop-filter: blur(12px); transition: all 0.3s ease; }
        .otp-code { background-color: #facc15; color: #000; padding: 2px 6px; border-radius: 4px; font-weight: bold; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        
        /* Scrollbar */
        ::-webkit-scrollbar { width: 6px; }
        ::-webkit-scrollbar-track { background: transparent; }
        ::-webkit-scrollbar-thumb { background: #cbd5e1; border-radius: 10px; }
        .dark ::-webkit-scrollbar-thumb { background: #475569; }
    </style>
</head>
<body class="min-h-screen flex flex-col items-center justify-center p-4 bg-gray-100 dark:bg-slate-900 text-gray-800 dark:text-gray-100 transition-colors duration-500">

    <div class="w-full max-w-2xl glass-panel bg-white/80 dark:bg-slate-800/80 border border-gray-200 dark:border-slate-700 rounded-2xl shadow-2xl p-6 relative z-10">
        
        <div class="flex items-center justify-between mb-6 border-b border-gray-200 dark:border-slate-700 pb-4">
            <div class="flex items-center gap-3">
                <div class="bg-blue-600 p-2 rounded-lg shadow-lg shadow-blue-500/30">
                    <i class="fa-solid fa-shield-cat text-white text-xl"></i>
                </div>
                <div>
                    <h1 class="text-xl font-bold tracking-wide">Buffalo Admin</h1>
                    <p class="text-[10px] text-blue-500 dark:text-blue-400 font-mono uppercase tracking-wider">Premium Temp Mail</p>
                </div>
            </div>
            
            <div class="flex gap-3">
                <button onclick="toggleTheme()" class="w-8 h-8 rounded-full bg-gray-200 dark:bg-slate-700 flex items-center justify-center hover:bg-gray-300 dark:hover:bg-slate-600 transition-all">
                    <i class="fa-solid fa-moon text-slate-800 dark:hidden"></i>
                    <i class="fa-solid fa-sun text-yellow-400 hidden dark:block"></i>
                </button>

                <button onclick="toggleHistory()" class="w-8 h-8 rounded-full bg-gray-200 dark:bg-slate-700 flex items-center justify-center hover:bg-gray-300 dark:hover:bg-slate-600 transition-all relative">
                    <i class="fa-solid fa-clock-rotate-left text-gray-600 dark:text-gray-300"></i>
                    <span id="history-count" class="absolute -top-1 -right-1 bg-red-500 text-white text-[9px] w-4 h-4 flex items-center justify-center rounded-full hidden">0</span>
                </button>
            </div>
        </div>

        <div id="history-panel" class="hidden bg-gray-50 dark:bg-slate-900/50 rounded-xl p-4 mb-4 border border-gray-200 dark:border-slate-700">
            <div class="flex justify-between items-center mb-3">
                <h3 class="text-xs font-bold uppercase tracking-wider opacity-70">History (Reuse Emails)</h3>
                <button onclick="clearHistory()" class="text-xs text-red-500 hover:text-red-600"><i class="fa-solid fa-trash"></i> Clear</button>
            </div>
            <div id="history-list" class="space-y-2 max-h-40 overflow-y-auto pr-2">
                </div>
        </div>

        <div class="bg-gray-50 dark:bg-slate-900/50 rounded-xl p-5 mb-6 border border-gray-200 dark:border-slate-700">
            <label class="text-[10px] text-blue-500 uppercase font-bold tracking-widest mb-2 block">Active Address</label>
            <div class="flex flex-col sm:flex-row gap-3">
                <div class="relative flex-grow group">
                    <input type="text" id="current-email" readonly 
                        class="w-full bg-white dark:bg-slate-900 font-mono text-lg py-3 px-4 rounded-lg border border-gray-300 dark:border-slate-600 focus:outline-none focus:border-blue-500 dark:focus:border-blue-500 transition-all text-center sm:text-left shadow-sm"
                        value="Loading...">
                    <button onclick="copyEmail()" class="absolute right-2 top-2 p-2 text-gray-400 hover:text-blue-500 transition-colors">
                        <i class="fa-regular fa-copy"></i>
                    </button>
                </div>
                <button onclick="generateNewEmail()" class="bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded-lg font-medium transition-all shadow-lg shadow-blue-500/30 flex items-center justify-center gap-2 whitespace-nowrap">
                    <i class="fa-solid fa-plus"></i> New
                </button>
            </div>
        </div>

        <div class="flex justify-between items-end mb-4 px-1">
            <h2 class="text-lg font-semibold flex items-center gap-2">
                <i class="fa-solid fa-inbox opacity-60"></i> Inbox
            </h2>
            <button onclick="fetchEmails()" class="text-xs bg-gray-200 dark:bg-slate-700 hover:bg-gray-300 dark:hover:bg-slate-600 px-3 py-1.5 rounded-full transition-colors flex items-center gap-2">
                <i class="fa-solid fa-rotate-right" id="refresh-icon"></i> Check Mail
            </button>
        </div>

        <div id="inbox" class="space-y-3 min-h-[250px]">
            <div class="text-center py-12 opacity-40">
                <i class="fa-regular fa-paper-plane text-5xl mb-4"></i>
                <p class="text-sm">Waiting for messages...</p>
            </div>
        </div>
    </div>

    <div id="toast" class="fixed bottom-8 bg-slate-800 dark:bg-white text-white dark:text-slate-900 px-6 py-3 rounded-full shadow-xl transform translate-y-24 opacity-0 transition-all duration-500 z-50 flex items-center gap-3 font-medium">
        <i class="fa-solid fa-check-circle text-green-500"></i>
        <span id="toast-msg">Done</span>
    </div>

    <script>
        const DOMAIN = "buffaloadmin.online"; 
        let currentEmail = "";
        let emailHistory = JSON.parse(localStorage.getItem("mail_history_v2")) || [];

        // --- THEME LOGIC ---
        function initTheme() {
            const theme = localStorage.getItem('theme');
            if (theme === 'light') {
                document.documentElement.classList.remove('dark');
            } else {
                document.documentElement.classList.add('dark');
            }
        }

        function toggleTheme() {
            const html = document.documentElement;
            if (html.classList.contains('dark')) {
                html.classList.remove('dark');
                localStorage.setItem('theme', 'light');
            } else {
                html.classList.add('dark');
                localStorage.setItem('theme', 'dark');
            }
        }
        // ------------------

        function init() {
            initTheme();
            // Load last email or create new
            const saved = localStorage.getItem("current_active_email");
            if (saved) {
                currentEmail = saved;
                addToHistory(saved); // Ensure it's in history
            } else {
                createRandomEmail();
            }
            updateDisplay();
            updateHistoryUI();
            
            setInterval(fetchEmails, 3000);
        }

        function createRandomEmail() {
            const randomStr = Math.random().toString(36).substring(7);
            const newEmail = randomStr + "@" + DOMAIN;
            setActiveEmail(newEmail);
            showToast("New address created!");
        }

        function setActiveEmail(email) {
            currentEmail = email;
            localStorage.setItem("current_active_email", currentEmail);
            addToHistory(email);
            
            // Reset Inbox UI
            document.getElementById("inbox").innerHTML = `
                <div class="text-center py-12 opacity-40 animate-pulse">
                    <i class="fa-solid fa-satellite-dish text-4xl mb-4"></i>
                    <p class="text-sm">Listening for ${email}...</p>
                </div>`;
            
            updateDisplay();
            fetchEmails(); // Check immediately
        }

        function addToHistory(email) {
            if (!emailHistory.includes(email)) {
                emailHistory.unshift(email);
                if (emailHistory.length > 10) emailHistory.pop();
                localStorage.setItem("mail_history_v2", JSON.stringify(emailHistory));
            }
            updateHistoryUI();
        }

        function updateHistoryUI() {
            const list = document.getElementById("history-list");
            const countBadge = document.getElementById("history-count");
            
            if (emailHistory.length > 0) {
                countBadge.innerText = emailHistory.length;
                countBadge.classList.remove("hidden");
                
                list.innerHTML = emailHistory.map(email => {
                    const isActive = email === currentEmail;
                    return `
                    <div onclick="restoreEmail('${email}')" 
                        class="flex justify-between items-center p-3 rounded-lg cursor-pointer transition-all border border-transparent
                        ${isActive ? 'bg-blue-100 dark:bg-blue-900/30 border-blue-500' : 'bg-white dark:bg-slate-800 hover:bg-gray-100 dark:hover:bg-slate-700'}">
                        <span class="text-xs font-mono truncate ${isActive ? 'text-blue-600 dark:text-blue-400 font-bold' : 'text-gray-600 dark:text-gray-400'}">${email}</span>
                        ${isActive ? '<span class="text-[10px] bg-blue-500 text-white px-2 rounded-full">Active</span>' : '<i class="fa-solid fa-rotate-left text-gray-400 hover:text-blue-500"></i>'}
                    </div>
                `}).join('');
            } else {
                countBadge.classList.add("hidden");
                list.innerHTML = '<div class="text-center text-xs opacity-50 py-2">No history</div>';
            }
        }

        function restoreEmail(email) {
            if (currentEmail === email) return;
            setActiveEmail(email);
            toggleHistory(); // Close panel
            showToast("Restored: Waiting for codes...");
        }

        function clearHistory() {
            if(confirm("Clear all history?")) {
                emailHistory = [];
                localStorage.removeItem("mail_history_v2");
                updateHistoryUI();
            }
        }

        function toggleHistory() {
            document.getElementById("history-panel").classList.toggle("hidden");
        }

        function updateDisplay() {
            document.getElementById("current-email").value = currentEmail;
            updateHistoryUI(); // To update the "Active" highlight
        }

        function copyEmail() {
            navigator.clipboard.writeText(currentEmail);
            showToast("Copied to clipboard");
        }

        function showToast(msg) {
            const toast = document.getElementById("toast");
            document.getElementById("toast-msg").innerText = msg;
            toast.classList.remove("translate-y-24", "opacity-0");
            setTimeout(() => toast.classList.add("translate-y-24", "opacity-0"), 3000);
        }

        async function fetchEmails() {
            if (!currentEmail) return;
            const icon = document.getElementById("refresh-icon");
            icon.classList.add("fa-spin");

            try {
                const res = await fetch(`/api/emails?address=${currentEmail}`);
                const data = await res.json();
                const inbox = document.getElementById("inbox");

                if (data.length > 0) {
                    inbox.innerHTML = data.reverse().map(msg => {
                        let body = msg.body.replace(/</g, "&lt;"); 
                        // Smart OTP Highlight
                        body = body.replace(/\\b\\d{4,8}\\b/g, match => `<span class="otp-code">${match}</span>`);
                        body = body.replace(/\\n/g, "<br>");

                        return `
                        <div class="bg-white dark:bg-slate-800 border border-gray-200 dark:border-slate-700 rounded-xl p-4 hover:border-blue-500 transition-all shadow-sm animate-fade-in">
                            <div class="flex justify-between items-start mb-2 border-b border-gray-100 dark:border-slate-700 pb-2">
                                <div class="font-bold text-sm truncate w-2/3">${msg.sender}</div>
                                <span class="text-[10px] text-gray-500 bg-gray-100 dark:bg-slate-900 px-2 py-1 rounded">Just now</span>
                            </div>
                            <div class="text-blue-600 dark:text-blue-400 font-medium text-sm mb-2">${msg.subject}</div>
                            <div class="text-gray-600 dark:text-gray-300 text-sm bg-gray-50 dark:bg-slate-900/50 p-3 rounded-lg font-mono overflow-x-auto">
                                ${body}
                            </div>
                        </div>`;
                    }).join("");
                }
            } catch (e) { console.error(e); }
            
            setTimeout(() => icon.classList.remove("fa-spin"), 500);
        }

        // Fade In Animation
        const style = document.createElement('style');
        style.innerHTML = `
            @keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
            .animate-fade-in { animation: fadeIn 0.3s ease-out forwards; }
        `;
        document.head.appendChild(style);

        init();
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
        # Memory များမသွားအောင် ထိန်းသိမ်းခြင်း
        if len(emails_db) > 200: emails_db.pop(0) 
    return jsonify({"status": "received"}), 200

@app.route('/api/emails')
def get_emails():
    target = request.args.get('address')
    my_msgs = [m for m in emails_db if m.get('recipient') == target]
    return jsonify(my_msgs)

if __name__ == '__main__':
    app.run()                    <p>Inbox cleared. Waiting for new emails...</p>
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
