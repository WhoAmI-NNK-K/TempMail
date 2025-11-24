from flask import Flask, request, jsonify, render_template_string
from datetime import datetime
import email
from email.policy import default

app = Flask(__name__)

# Database
user_inboxes = {}

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
            theme: { extend: { colors: { brand: { 500: '#3b82f6', 600: '#2563eb' } } } }
        }
    </script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        .hide-scrollbar::-webkit-scrollbar { display: none; }
        .hide-scrollbar { -ms-overflow-style: none; scrollbar-width: none; }
        /* Iframe Responsive Fix */
        #email-frame { width: 100%; height: 100%; border: none; background: white; }
    </style>
</head>
<body class="bg-gray-50 dark:bg-slate-900 text-slate-800 dark:text-slate-100 min-h-screen flex flex-col transition-colors duration-300 overflow-hidden">

    <div class="bg-white dark:bg-slate-800 p-4 shadow-sm z-20 flex justify-between items-center px-4 safe-area-top">
        <div class="flex items-center gap-3">
            <div class="w-10 h-10 rounded-full bg-blue-600 text-white flex items-center justify-center font-bold text-lg shadow-lg">B</div>
            <div>
                <h1 class="font-bold text-lg leading-tight">Inbox</h1>
                <p class="text-[10px] text-green-500 font-mono flex items-center gap-1"><span class="w-2 h-2 rounded-full bg-green-500 animate-pulse"></span> Gmail Mode</p>
            </div>
        </div>
        <div class="flex gap-3">
            <button onclick="toggleTheme()" class="w-10 h-10 rounded-full bg-gray-100 dark:bg-slate-700 flex items-center justify-center transition">
                <i class="fa-solid fa-moon dark:hidden"></i><i class="fa-solid fa-sun hidden dark:block text-yellow-400"></i>
            </button>
            <button onclick="openHistory()" class="relative w-10 h-10 rounded-full bg-gray-100 dark:bg-slate-700 flex items-center justify-center transition">
                <i class="fa-solid fa-clock-rotate-left text-blue-500"></i>
                <span id="total-badge" class="absolute -top-1 -right-1 bg-red-500 text-white text-[10px] min-w-[18px] h-[18px] flex items-center justify-center rounded-full hidden shadow-sm border-2 border-white dark:border-slate-800">0</span>
            </button>
        </div>
    </div>

    <div class="flex-1 overflow-y-auto pb-24 px-4 pt-4 hide-scrollbar" id="main-scroll">
        
        <div class="bg-white dark:bg-slate-800 rounded-2xl p-5 shadow-lg border border-gray-100 dark:border-slate-700 mb-6 relative overflow-hidden group">
            <div class="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-blue-500 to-indigo-600"></div>
            
            <div class="flex justify-between items-center mb-2">
                <label class="text-[10px] font-bold text-gray-400 uppercase tracking-wider">Active Address</label>
                <button onclick="generateNewEmail()" class="text-[10px] bg-slate-900 dark:bg-white text-white dark:text-slate-900 px-3 py-1 rounded-full font-bold shadow-md hover:scale-105 transition">+ NEW</button>
            </div>
            
            <div class="flex items-center justify-between bg-gray-50 dark:bg-slate-900 p-3 rounded-xl border border-gray-200 dark:border-slate-700 mb-3 cursor-pointer active:scale-95 transition" onclick="copyEmail()">
                <span id="current-email" class="font-mono text-lg font-semibold text-blue-600 dark:text-blue-400 truncate w-[85%]">Loading...</span>
                <i class="fa-regular fa-copy text-gray-400"></i>
            </div>
            
             <button onclick="manualRefresh()" class="w-full bg-blue-50 dark:bg-slate-700/50 text-blue-600 dark:text-blue-300 py-2 rounded-lg text-xs font-bold flex items-center justify-center gap-2 hover:bg-blue-100 dark:hover:bg-slate-700 transition">
                <i id="refresh-icon" class="fa-solid fa-rotate-right"></i> Check Messages
            </button>
        </div>

        <h2 class="text-xs font-bold text-gray-400 uppercase tracking-widest mb-3 ml-1 flex justify-between">
            Messages <span id="msg-count" class="text-gray-500 bg-gray-200 dark:bg-slate-800 px-2 rounded text-[10px] flex items-center">0</span>
        </h2>
        
        <div id="inbox" class="space-y-3 pb-10">
            <div class="text-center py-10 opacity-40">
                <i class="fa-regular fa-envelope-open text-5xl mb-3"></i>
                <p class="text-sm">Waiting for emails...</p>
            </div>
        </div>
    </div>

    <div id="read-modal" class="fixed inset-0 z-50 hidden">
        <div class="absolute inset-0 bg-black/80 backdrop-blur-sm transition-opacity" onclick="closeReadModal()"></div>
        <div id="read-content-box" class="absolute bottom-0 left-0 w-full h-[95vh] bg-white dark:bg-slate-900 rounded-t-3xl shadow-2xl flex flex-col transform transition-transform duration-300 translate-y-full">
            
            <div class="p-4 border-b border-gray-100 dark:border-slate-700 flex justify-between items-center sticky top-0 bg-white/95 dark:bg-slate-900/95 backdrop-blur z-10 rounded-t-3xl">
                <button onclick="closeReadModal()" class="w-8 h-8 rounded-full bg-gray-100 dark:bg-slate-800 flex items-center justify-center hover:bg-gray-200 dark:hover:bg-slate-700 transition"><i class="fa-solid fa-chevron-down text-gray-500"></i></button>
                <span class="font-bold text-sm">Full Email View</span>
                <div class="w-8"></div>
            </div>

            <div class="flex-1 overflow-hidden flex flex-col bg-white">
                <div class="p-4 border-b border-gray-100 shrink-0">
                    <h2 id="read-subject" class="text-lg font-bold mb-1 text-slate-800 leading-tight">Subject</h2>
                    <div class="flex items-center gap-2">
                         <div class="w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center text-blue-600 font-bold text-xs" id="read-avatar">A</div>
                         <div>
                             <p id="read-sender" class="font-bold text-sm text-slate-700 truncate max-w-[200px]">Sender</p>
                             <p id="read-date" class="text-[10px] text-gray-400">Date</p>
                         </div>
                    </div>
                </div>
                
                <div class="flex-1 relative w-full bg-white">
                    <iframe id="email-frame" sandbox="allow-same-origin" class="absolute inset-0 w-full h-full"></iframe>
                </div>
            </div>
        </div>
    </div>

    <div id="history-overlay" class="fixed inset-0 z-40 hidden bg-black/50 backdrop-blur-sm transition-opacity opacity-0" onclick="closeHistory()"></div>
    <div id="history-panel" class="fixed bottom-0 left-0 w-full bg-white dark:bg-slate-800 rounded-t-3xl z-50 p-6 shadow-2xl transform translate-y-full transition-transform duration-300 max-h-[75vh] flex flex-col">
        <div class="w-12 h-1.5 bg-gray-300 dark:bg-slate-600 rounded-full mx-auto mb-6"></div>
        <div class="flex justify-between items-center mb-4">
            <h3 class="text-lg font-bold">Switch Account</h3>
            <button onclick="clearHistory()" class="text-red-500 text-xs font-bold uppercase hover:bg-red-50 px-2 py-1 rounded transition">Clear All</button>
        </div>
        <div id="history-list" class="overflow-y-auto space-y-2 flex-1 pr-1 pb-4 hide-scrollbar"></div>
    </div>

    <div id="toast" class="fixed top-6 left-1/2 -translate-x-1/2 bg-slate-800 text-white px-6 py-3 rounded-full shadow-2xl z-[60] flex items-center gap-3 transition-all duration-300 opacity-0 -translate-y-10 pointer-events-none">
        <span id="toast-msg">OK</span>
    </div>

    <script>
        const DOMAIN = "buffaloadmin.online";
        let currentEmail = "";
        let emailHistory = JSON.parse(localStorage.getItem("buffalo_hist_v8")) || [];
        let msgCounts = JSON.parse(localStorage.getItem("buffalo_counts_v8")) || {};

        function init() {
            if (localStorage.getItem('theme') === 'light') document.documentElement.classList.remove('dark');
            const saved = localStorage.getItem("buffalo_active_v8");
            if (saved) { switchAccount(saved, false); } else { generateNewEmail(); }
            setInterval(() => { if(currentEmail) fetchEmails(true); }, 3000);
        }

        function generateNewEmail() {
            const random = Math.random().toString(36).substring(7);
            const newEmail = random + "@" + DOMAIN;
            switchAccount(newEmail);
            showToast("New address created");
        }

        function switchAccount(email, saveHist = true) {
            currentEmail = email;
            localStorage.setItem("buffalo_active_v8", email);
            document.getElementById("current-email").innerText = email;
            document.getElementById("inbox").innerHTML = `
                <div class="text-center py-20 animate-pulse">
                     <div class="w-16 h-16 bg-blue-100 dark:bg-blue-900/30 rounded-full flex items-center justify-center mx-auto mb-4"><i class="fa-solid fa-satellite-dish text-2xl text-blue-500"></i></div>
                    <p class="text-sm text-gray-500">Connecting...</p>
                </div>`;
            document.getElementById("msg-count").innerText = "0";
            
            if (saveHist) {
                if (!emailHistory.includes(email)) emailHistory.unshift(email);
                if (emailHistory.length > 20) emailHistory.pop();
                localStorage.setItem("buffalo_hist_v8", JSON.stringify(emailHistory));
            }
            closeHistory(); fetchEmails(false);
        }

        async function fetchEmails(silent = false) {
            if (!currentEmail) return;
            const icon = document.getElementById("refresh-icon");
            if(!silent) icon.classList.add("fa-spin");

            try {
                const res = await fetch(`/api/emails?address=${currentEmail}`);
                const data = await res.json();
                
                document.getElementById("msg-count").innerText = data.length;
                msgCounts[currentEmail] = data.length;
                localStorage.setItem("buffalo_counts_v8", JSON.stringify(msgCounts));
                updateHistoryBadges();

                const inbox = document.getElementById("inbox");
                if (data.length > 0) {
                    inbox.innerHTML = data.reverse().map((msg, index) => {
                        const safeSender = msg.sender.replace(/'/g, "&apos;");
                        const safeSubject = msg.subject.replace(/'/g, "&apos;");
                        // Store full HTML content safely
                        const safeHtml = encodeURIComponent(msg.html_content || msg.body);
                        
                        return `
                        <div onclick="openReadModal('${safeSender}', '${safeSubject}', '${safeHtml}', '${msg.timestamp}')" 
                            class="bg-white dark:bg-slate-800 p-4 rounded-2xl shadow-sm border border-gray-100 dark:border-slate-700 relative overflow-hidden group active:scale-[0.98] transition cursor-pointer hover:shadow-md">
                            <div class="flex justify-between items-start mb-1">
                                <div class="font-bold text-sm text-slate-800 dark:text-slate-100 truncate w-[70%]">${msg.sender}</div>
                                <span class="text-[10px] text-gray-400 font-mono">${msg.timestamp}</span>
                            </div>
                            <div class="font-bold text-blue-600 dark:text-blue-400 text-sm mb-1 truncate">${msg.subject}</div>
                            <div class="text-xs text-gray-500 dark:text-slate-400 truncate">Tap to open email</div>
                        </div>`;
                    }).join("");
                } else if (!silent) {
                    inbox.innerHTML = '<div class="text-center py-10 opacity-40"><i class="fa-regular fa-envelope-open text-5xl mb-3"></i><p class="text-sm">No messages yet</p></div>';
                }
            } catch (e) { console.error(e); }
            if(!silent) setTimeout(() => icon.classList.remove("fa-spin"), 500);
        }

        function openReadModal(sender, subject, encodedHtml, date) {
            const htmlContent = decodeURIComponent(encodedHtml);
            
            document.getElementById("read-sender").innerText = sender;
            document.getElementById("read-avatar").innerText = sender.charAt(0).toUpperCase();
            document.getElementById("read-subject").innerText = subject;
            document.getElementById("read-date").innerText = date;
            
            // Inject into Iframe to render like native Gmail
            const iframe = document.getElementById("email-frame");
            iframe.srcdoc = htmlContent;
            
            const modal = document.getElementById("read-modal");
            const box = document.getElementById("read-content-box");
            modal.classList.remove("hidden");
            setTimeout(() => { box.classList.remove("translate-y-full"); }, 10);
        }

        function closeReadModal() {
            const box = document.getElementById("read-content-box");
            box.classList.add("translate-y-full");
            setTimeout(() => { document.getElementById("read-modal").classList.add("hidden"); }, 300);
        }

        function openHistory() {
            updateHistoryBadges();
            const list = document.getElementById("history-list");
            if (emailHistory.length > 0) {
                list.innerHTML = emailHistory.map(email => {
                    const isActive = email === currentEmail;
                    const count = msgCounts[email] || 0;
                    return `
                    <div onclick="switchAccount('${email}')" class="p-3 rounded-xl flex items-center justify-between cursor-pointer transition mb-2 ${isActive ? 'bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800' : 'bg-gray-50 dark:bg-slate-700/50 active:bg-gray-200'}">
                        <div class="flex items-center gap-3 overflow-hidden">
                            <div class="w-8 h-8 rounded-full ${isActive ? 'bg-blue-500' : 'bg-gray-300 dark:bg-slate-600'} flex items-center justify-center text-white font-bold text-xs">${email.charAt(0).toUpperCase()}</div>
                            <div class="flex flex-col overflow-hidden"><span class="font-mono text-xs font-bold truncate ${isActive ? 'text-blue-600 dark:text-blue-400' : 'text-gray-700 dark:text-gray-300'}">${email}</span></div>
                        </div>
                        ${count > 0 ? `<span class="bg-red-500 text-white text-[10px] font-bold px-2 py-0.5 rounded-full shadow-sm">${count}</span>` : (isActive ? '<i class="fa-solid fa-check text-blue-500"></i>' : '')}
                    </div>`;
                }).join('');
            } else { list.innerHTML = '<p class="text-center text-gray-400 text-sm mt-4">No history</p>'; }
            document.getElementById("history-overlay").classList.remove("hidden");
            setTimeout(() => { document.getElementById("history-overlay").classList.remove("opacity-0"); document.getElementById("history-panel").classList.remove("translate-y-full"); }, 10);
        }

        function closeHistory() {
            document.getElementById("history-overlay").classList.add("opacity-0");
            document.getElementById("history-panel").classList.add("translate-y-full");
            setTimeout(() => { document.getElementById("history-overlay").classList.add("hidden"); }, 300);
        }
        
        function updateHistoryBadges() {
            let total = 0; emailHistory.forEach(e => { if(msgCounts[e]) total += msgCounts[e]; });
            const badge = document.getElementById("total-badge");
            if(total > 0) { badge.innerText = total > 9 ? '9+' : total; badge.classList.remove("hidden"); } 
            else { badge.classList.add("hidden"); }
        }

        function clearHistory() { if(confirm("Clear history?")) { emailHistory = []; msgCounts = {}; localStorage.removeItem("buffalo_hist_v8"); localStorage.removeItem("buffalo_counts_v8"); closeHistory(); }}
        function manualRefresh() { fetchEmails(); }
        function toggleTheme() { if (document.documentElement.classList.contains('dark')) { document.documentElement.classList.remove('dark'); localStorage.setItem('theme', 'light'); } else { document.documentElement.classList.add('dark'); localStorage.setItem('theme', 'dark'); }}
        function copyEmail() { navigator.clipboard.writeText(currentEmail); showToast("Copied!"); }
        function showToast(msg) { const t = document.getElementById("toast"); document.getElementById("toast-msg").innerText = msg; t.classList.remove("opacity-0", "-translate-y-10"); setTimeout(() => t.classList.add("opacity-0", "-translate-y-10"), 2000); }

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
        now = datetime.now().strftime("%H:%M")
        raw_body = data.get('body', '')
        
        # --- GMAIL-STYLE PARSER ---
        # HTML ကို ဦးစားပေးပြီး သီးသန့်ခွဲထုတ်မယ်
        html_content = ""
        text_content = ""
        
        try:
            msg = email.message_from_string(raw_body, policy=default)
            if msg['subject']: data['subject'] = msg['subject']
            
            if msg.is_multipart():
                for part in msg.walk():
                    ctype = part.get_content_type()
                    # HTML အပိုင်းကို ရှာပြီး သိမ်းမယ်
                    if ctype == 'text/html':
                        html_content = part.get_content()
                    elif ctype == 'text/plain':
                        text_content = part.get_content()
            else:
                if msg.get_content_type() == 'text/html':
                    html_content = msg.get_content()
                else:
                    text_content = msg.get_content()

        except Exception: pass
        
        # HTML ရှိရင် HTML ကို Frontend ပို့မယ်၊ မရှိရင် Text ကို ပို့မယ်
        data['html_content'] = html_content if html_content else text_content
        data['body'] = text_content if text_content else "Open to view content"
        # ---------------------------

        data['timestamp'] = now
        recipient = data.get('recipient')
        if recipient:
            if recipient not in user_inboxes: user_inboxes[recipient] = []
            user_inboxes[recipient].append(data)
            if len(user_inboxes[recipient]) > 50: user_inboxes[recipient].pop(0)
            
    return jsonify({"status": "received"}), 200

@app.route('/api/emails')
def get_emails():
    target = request.args.get('address')
    my_msgs = user_inboxes.get(target, [])
    return jsonify(my_msgs)

if __name__ == '__main__':
    app.run()
