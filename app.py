from flask import Flask, request, jsonify, render_template_string

app = Flask(__name__)

# Server Memory
emails_db = []

HTML_PAGE = """
<!DOCTYPE html>
<html lang="en" class="dark">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>Buffalo Admin</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script>
        tailwind.config = {
            darkMode: 'class',
            theme: {
                extend: {
                    colors: {
                        brand: { 500: '#3b82f6', 600: '#2563eb' },
                        dark: { bg: '#0f172a', card: '#1e293b' }
                    }
                }
            }
        }
    </script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        body { -webkit-tap-highlight-color: transparent; }
        .otp-badge { background: #facc15; color: black; padding: 2px 6px; border-radius: 4px; font-weight: 800; font-family: monospace; border: 1px solid #eab308; display: inline-block; margin: 2px 0; }
        .history-modal { transition: transform 0.3s ease-in-out; }
        .hide-modal { transform: translateY(100%); }
        .show-modal { transform: translateY(0); }
        
        /* Gmail-like Avatar */
        .avatar { background: linear-gradient(135deg, #3b82f6, #8b5cf6); color: white; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 20px; }
    </style>
</head>
<body class="bg-gray-100 dark:bg-slate-900 text-slate-800 dark:text-slate-100 min-h-screen flex flex-col transition-colors duration-300">

    <div class="bg-white dark:bg-slate-800 p-4 shadow-sm sticky top-0 z-20 flex justify-between items-center px-6">
        <div class="flex items-center gap-3">
            <div class="w-10 h-10 rounded-full avatar shadow-lg">B</div>
            <div>
                <h1 class="font-bold text-lg leading-tight">Inbox</h1>
                <p class="text-[10px] text-gray-500 dark:text-gray-400 font-mono">buffaloadmin.online</p>
            </div>
        </div>
        
        <div class="flex gap-4">
            <button onclick="toggleTheme()" class="w-10 h-10 rounded-full hover:bg-gray-100 dark:hover:bg-slate-700 flex items-center justify-center transition">
                <i class="fa-solid fa-moon dark:hidden text-xl text-gray-600"></i>
                <i class="fa-solid fa-sun hidden dark:block text-xl text-yellow-400"></i>
            </button>
            <button onclick="openHistory()" class="relative w-10 h-10 rounded-full hover:bg-gray-100 dark:hover:bg-slate-700 flex items-center justify-center transition">
                <i class="fa-solid fa-layer-group text-xl text-brand-500"></i>
                <span id="history-badge" class="absolute top-1 right-1 w-3 h-3 bg-red-500 rounded-full border-2 border-white dark:border-slate-800 hidden"></span>
            </button>
        </div>
    </div>

    <div class="p-4 mx-2 mt-2">
        <div class="bg-white dark:bg-slate-800 rounded-2xl p-5 shadow-lg border border-gray-100 dark:border-slate-700 relative overflow-hidden">
            <div class="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-blue-500 to-purple-500"></div>
            
            <label class="text-xs font-bold text-gray-400 uppercase tracking-wider mb-2 block">Current Active Address</label>
            
            <div class="flex flex-col gap-4">
                <div class="flex items-center justify-between bg-gray-50 dark:bg-slate-900 p-3 rounded-xl border border-gray-200 dark:border-slate-700">
                    <span id="current-email" class="font-mono text-lg font-semibold text-blue-600 dark:text-blue-400 truncate select-all">Loading...</span>
                    <button onclick="copyEmail()" class="text-gray-400 hover:text-blue-500 px-2">
                        <i class="fa-regular fa-copy text-xl"></i>
                    </button>
                </div>

                <div class="flex gap-3">
                    <button onclick="generateNewEmail()" class="flex-1 bg-slate-900 dark:bg-white text-white dark:text-slate-900 py-3 rounded-xl font-bold text-sm shadow hover:opacity-90 active:scale-95 transition flex items-center justify-center gap-2">
                        <i class="fa-solid fa-plus"></i> Create New
                    </button>
                    <button onclick="fetchEmails()" class="w-12 bg-gray-200 dark:bg-slate-700 text-gray-600 dark:text-white rounded-xl flex items-center justify-center hover:bg-gray-300 active:scale-95 transition">
                        <i id="refresh-icon" class="fa-solid fa-rotate-right"></i>
                    </button>
                </div>
            </div>
        </div>
    </div>

    <div class="flex-1 px-4 pb-20">
        <h2 class="text-xs font-bold text-gray-400 uppercase tracking-widest mb-3 ml-2 mt-4">Messages</h2>
        <div id="inbox" class="space-y-3">
            <div class="text-center py-20 opacity-50">
                <i class="fa-regular fa-envelope-open text-6xl mb-4 text-gray-300 dark:text-slate-600"></i>
                <p>Waiting for emails...</p>
            </div>
        </div>
    </div>

    <div id="history-overlay" class="fixed inset-0 bg-black/50 z-40 hidden backdrop-blur-sm" onclick="closeHistory()"></div>
    <div id="history-panel" class="fixed bottom-0 left-0 w-full bg-white dark:bg-slate-800 rounded-t-3xl z-50 p-6 shadow-2xl history-modal hide-modal max-h-[70vh] flex flex-col">
        <div class="w-12 h-1.5 bg-gray-300 dark:bg-slate-600 rounded-full mx-auto mb-6"></div>
        
        <div class="flex justify-between items-center mb-4">
            <h3 class="text-lg font-bold">Switch Account</h3>
            <button onclick="clearHistory()" class="text-red-500 text-sm font-medium hover:underline">Clear All</button>
        </div>

        <div id="history-list" class="overflow-y-auto space-y-2 flex-1 pr-1">
            </div>
    </div>

    <div id="toast" class="fixed top-5 left-1/2 transform -translate-x-1/2 bg-slate-800 text-white px-6 py-3 rounded-full shadow-xl z-[60] flex items-center gap-2 transition-all duration-300 opacity-0 -translate-y-10 pointer-events-none">
        <i class="fa-solid fa-check-circle text-green-400"></i>
        <span id="toast-msg">Notification</span>
    </div>

    <script>
        const DOMAIN = "buffaloadmin.online";
        let currentEmail = "";
        let emailHistory = JSON.parse(localStorage.getItem("mail_history_v3")) || [];

        // --- Core Functions ---

        function init() {
            // Theme Init
            if (localStorage.getItem('theme') === 'light') {
                document.documentElement.classList.remove('dark');
            }
            
            // Load Email
            const saved = localStorage.getItem("active_email_v3");
            if (saved) {
                switchAccount(saved, false); // false = don't animate yet
            } else {
                generateNewEmail();
            }
            
            updateHistoryUI();
            
            // Auto Refresh Loop
            setInterval(() => {
                if(currentEmail) fetchEmails(true);
            }, 3000);
        }

        // 1. New Button Function (Fixed)
        function generateNewEmail() {
            const random = Math.random().toString(36).substring(7);
            const newEmail = random + "@" + DOMAIN;
            switchAccount(newEmail);
            showToast("New address created!");
        }

        // 2. Switch Account Logic (The "Gmail" feel)
        function switchAccount(email, saveToHist = true) {
            currentEmail = email;
            localStorage.setItem("active_email_v3", email);
            
            // UI Updates
            document.getElementById("current-email").innerText = email;
            
            // Reset Inbox Visuals
            document.getElementById("inbox").innerHTML = `
                <div class="text-center py-20 animate-pulse">
                    <div class="w-16 h-16 bg-blue-100 dark:bg-blue-900/30 rounded-full flex items-center justify-center mx-auto mb-4">
                        <i class="fa-solid fa-satellite-dish text-2xl text-blue-500"></i>
                    </div>
                    <p class="text-sm font-medium text-gray-500">Listening...</p>
                </div>`;

            if (saveToHist) addToHistory(email);
            
            closeHistory(); // Close modal if open
            fetchEmails(false); // Fetch immediately
        }

        function addToHistory(email) {
            // Remove if exists (to move to top)
            emailHistory = emailHistory.filter(e => e !== email);
            emailHistory.unshift(email);
            // Limit to 15
            if (emailHistory.length > 15) emailHistory.pop();
            
            localStorage.setItem("mail_history_v3", JSON.stringify(emailHistory));
            updateHistoryUI();
        }

        // 3. Render History List
        function updateHistoryUI() {
            const list = document.getElementById("history-list");
            const badge = document.getElementById("history-badge");
            
            if (emailHistory.length > 0) {
                badge.classList.remove("hidden");
                list.innerHTML = emailHistory.map(email => {
                    const isActive = email === currentEmail;
                    return `
                    <div onclick="switchAccount('${email}')" class="p-4 rounded-xl flex items-center justify-between cursor-pointer transition ${isActive ? 'bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800' : 'hover:bg-gray-50 dark:hover:bg-slate-700'}">
                        <div class="flex items-center gap-3 overflow-hidden">
                            <div class="w-8 h-8 rounded-full ${isActive ? 'bg-blue-500' : 'bg-gray-300 dark:bg-slate-600'} flex items-center justify-center text-white font-bold text-xs">
                                ${email.charAt(0).toUpperCase()}
                            </div>
                            <div class="flex flex-col overflow-hidden">
                                <span class="font-mono text-sm truncate ${isActive ? 'font-bold text-blue-600 dark:text-blue-400' : 'text-gray-700 dark:text-gray-300'}">${email}</span>
                                <span class="text-[10px] text-gray-400">${isActive ? 'Active Now' : 'Tap to switch'}</span>
                            </div>
                        </div>
                        ${isActive ? '<i class="fa-solid fa-check-circle text-blue-500"></i>' : ''}
                    </div>
                    `;
                }).join('');
            } else {
                badge.classList.add("hidden");
                list.innerHTML = '<p class="text-center text-gray-400 text-sm mt-10">No history yet</p>';
            }
        }

        // 4. Fetch Emails & Display
        async function fetchEmails(silent = false) {
            if (!currentEmail) return;
            const icon = document.getElementById("refresh-icon");
            if(!silent) icon.classList.add("fa-spin");

            try {
                const res = await fetch(`/api/emails?address=${currentEmail}`);
                const data = await res.json();
                const inbox = document.getElementById("inbox");

                if (data.length > 0) {
                    inbox.innerHTML = data.reverse().map(msg => {
                        let body = msg.body.replace(/</g, "&lt;");
                        // OTP Smart Highlight
                        body = body.replace(/\\b\\d{4,8}\\b/g, match => `<span class="otp-badge">${match}</span>`);
                        body = body.replace(/\\n/g, "<br>");

                        return `
                        <div class="bg-white dark:bg-slate-800 p-4 rounded-2xl shadow-sm border border-gray-100 dark:border-slate-700 relative overflow-hidden group">
                            <div class="absolute top-0 left-0 w-1 h-full bg-blue-500"></div>
                            <div class="flex justify-between items-start mb-2 pl-2">
                                <div class="font-bold text-sm text-slate-700 dark:text-slate-200">${msg.sender}</div>
                                <span class="text-[10px] font-bold text-blue-500 bg-blue-50 dark:bg-blue-900/30 px-2 py-1 rounded-full">NOW</span>
                            </div>
                            <div class="pl-2 mb-2 font-semibold text-sm text-slate-800 dark:text-white">${msg.subject}</div>
                            <div class="pl-2 text-sm text-slate-500 dark:text-slate-400 font-mono bg-gray-50 dark:bg-slate-900/50 p-3 rounded-lg border border-gray-100 dark:border-slate-700 overflow-x-auto">
                                ${body}
                            </div>
                        </div>`;
                    }).join("");
                }
            } catch (e) { console.error(e); }
            
            if(!silent) setTimeout(() => icon.classList.remove("fa-spin"), 500);
        }

        // --- UI Helpers ---
        function openHistory() {
            document.getElementById("history-overlay").classList.remove("hidden");
            const panel = document.getElementById("history-panel");
            panel.classList.remove("hide-modal");
            panel.classList.add("show-modal");
        }

        function closeHistory() {
            const panel = document.getElementById("history-panel");
            panel.classList.remove("show-modal");
            panel.classList.add("hide-modal");
            setTimeout(() => {
                document.getElementById("history-overlay").classList.add("hidden");
            }, 300);
        }
        
        function clearHistory() {
            if(confirm("Clear history?")) {
                emailHistory = [];
                localStorage.removeItem("mail_history_v3");
                updateHistoryUI();
            }
        }

        function toggleTheme() {
            const html = document.documentElement;
            if (html.classList.contains('dark')) {
                html.classList.remove('dark'); localStorage.setItem('theme', 'light');
            } else {
                html.classList.add('dark'); localStorage.setItem('theme', 'dark');
            }
        }

        function copyEmail() {
            navigator.clipboard.writeText(currentEmail);
            showToast("Address Copied!");
        }

        function showToast(msg) {
            const toast = document.getElementById("toast");
            document.getElementById("toast-msg").innerText = msg;
            toast.classList.remove("opacity-0", "-translate-y-10");
            setTimeout(() => toast.classList.add("opacity-0", "-translate-y-10"), 2000);
        }

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
        if len(emails_db) > 200: emails_db.pop(0)
    return jsonify({"status": "received"}), 200

@app.route('/api/emails')
def get_emails():
    target = request.args.get('address')
    my_msgs = [m for m in emails_db if m.get('recipient') == target]
    return jsonify(my_msgs)

if __name__ == '__main__':
    app.run()
