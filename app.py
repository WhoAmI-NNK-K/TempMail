from flask import Flask, request, jsonify, render_template_string
from datetime import datetime

app = Flask(__name__)

# Database (In-Memory)
# Structure: { "email_address": [ {msg1}, {msg2} ] }
# ဒီလိုသိမ်းမှ အကောင့်ပြောင်းလိုက်ရင် စာတွေမပျောက်ဘဲ ကျန်နေမှာပါ
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
            theme: {
                extend: {
                    colors: { brand: { 500: '#3b82f6', 600: '#2563eb' } }
                }
            }
        }
    </script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        .otp-badge { background: #facc15; color: black; padding: 2px 6px; border-radius: 4px; font-weight: 800; border: 1px solid #eab308; display: inline-block; cursor: pointer; }
        .modal-enter { transform: translateY(100%); opacity: 0; }
        .modal-enter-active { transform: translateY(0); opacity: 1; transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1); }
        .modal-exit { transform: translateY(0); opacity: 1; }
        .modal-exit-active { transform: translateY(100%); opacity: 0; transition: all 0.2s ease-in; }
    </style>
</head>
<body class="bg-gray-50 dark:bg-slate-900 text-slate-800 dark:text-slate-100 min-h-screen flex flex-col transition-colors duration-300 overflow-hidden">

    <div class="bg-white dark:bg-slate-800 p-4 shadow-sm z-20 flex justify-between items-center px-4 safe-area-top">
        <div class="flex items-center gap-3">
            <div class="w-10 h-10 rounded-full bg-gradient-to-br from-blue-500 to-indigo-600 text-white flex items-center justify-center font-bold text-lg shadow-lg">B</div>
            <div>
                <h1 class="font-bold text-lg leading-tight">Inbox</h1>
                <p id="status-text" class="text-[10px] text-green-500 font-mono flex items-center gap-1">
                    <span class="w-2 h-2 rounded-full bg-green-500 animate-pulse"></span> Live
                </p>
            </div>
        </div>
        <div class="flex gap-3">
             <button onclick="toggleTheme()" class="w-10 h-10 rounded-full bg-gray-100 dark:bg-slate-700 flex items-center justify-center">
                <i class="fa-solid fa-moon dark:hidden"></i><i class="fa-solid fa-sun hidden dark:block text-yellow-400"></i>
            </button>
            <button onclick="openHistory()" class="relative w-10 h-10 rounded-full bg-gray-100 dark:bg-slate-700 flex items-center justify-center">
                <i class="fa-solid fa-layer-group text-blue-500"></i>
                <span id="total-badge" class="absolute -top-1 -right-1 bg-red-500 text-white text-[10px] min-w-[18px] h-[18px] flex items-center justify-center rounded-full hidden shadow-sm border-2 border-white dark:border-slate-800">0</span>
            </button>
        </div>
    </div>

    <div class="flex-1 overflow-y-auto pb-24 px-4 pt-4" id="main-scroll">
        
        <div class="bg-white dark:bg-slate-800 rounded-2xl p-5 shadow-lg border border-gray-100 dark:border-slate-700 mb-6 relative overflow-hidden group">
            <div class="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-blue-500 via-indigo-500 to-purple-500"></div>
            
            <div class="flex justify-between items-center mb-2">
                <label class="text-[10px] font-bold text-gray-400 uppercase tracking-wider">Active Address</label>
                <button onclick="generateNewEmail()" class="text-[10px] bg-slate-900 dark:bg-white text-white dark:text-slate-900 px-3 py-1 rounded-full font-bold shadow-md hover:scale-105 transition">
                    + NEW
                </button>
            </div>
            
            <div class="flex items-center justify-between bg-gray-50 dark:bg-slate-900 p-3 rounded-xl border border-gray-200 dark:border-slate-700 mb-3" onclick="copyEmail()">
                <span id="current-email" class="font-mono text-lg font-semibold text-blue-600 dark:text-blue-400 truncate w-[85%]">Loading...</span>
                <i class="fa-regular fa-copy text-gray-400"></i>
            </div>
            
             <button onclick="manualRefresh()" class="w-full bg-blue-50 dark:bg-slate-700/50 text-blue-600 dark:text-blue-300 py-2 rounded-lg text-xs font-bold flex items-center justify-center gap-2 hover:bg-blue-100 transition">
                <i id="refresh-icon" class="fa-solid fa-rotate-right"></i> Check for New Messages
            </button>
        </div>

        <h2 class="text-xs font-bold text-gray-400 uppercase tracking-widest mb-3 ml-1 flex justify-between">
            Messages <span id="msg-count" class="text-gray-500">0</span>
        </h2>
        
        <div id="inbox" class="space-y-3 pb-10">
            <div class="text-center py-10 opacity-40">
                <i class="fa-regular fa-envelope-open text-5xl mb-3"></i>
                <p class="text-sm">No messages yet</p>
            </div>
        </div>
    </div>

    <div id="read-modal" class="fixed inset-0 z-50 hidden">
        <div class="absolute inset-0 bg-black/60 backdrop-blur-sm" onclick="closeReadModal()"></div>
        <div id="read-content-box" class="absolute bottom-0 left-0 w-full h-[85vh] bg-white dark:bg-slate-900 rounded-t-3xl shadow-2xl flex flex-col transform transition-transform duration-300 translate-y-full">
            
            <div class="p-4 border-b border-gray-100 dark:border-slate-700 flex justify-between items-center bg-white/50 dark:bg-slate-900/50 backdrop-blur-md rounded-t-3xl sticky top-0 z-10">
                <button onclick="closeReadModal()" class="w-8 h-8 rounded-full bg-gray-100 dark:bg-slate-800 flex items-center justify-center">
                    <i class="fa-solid fa-chevron-down text-gray-500"></i>
                </button>
                <span class="font-bold text-sm">Message Details</span>
                <div class="w-8"></div>
            </div>

            <div class="flex-1 overflow-y-auto p-6">
                <div class="flex items-center gap-3 mb-6">
                    <div class="w-12 h-12 rounded-full bg-blue-100 dark:bg-blue-900/30 flex items-center justify-center text-blue-600 dark:text-blue-400 font-bold text-xl" id="read-avatar">
                        A
                    </div>
                    <div>
                        <h3 id="read-sender" class="font-bold text-lg leading-tight">Sender Name</h3>
                        <p id="read-date" class="text-xs text-gray-400 mt-1">Today, 10:23 AM</p>
                    </div>
                </div>

                <h2 id="read-subject" class="text-xl font-bold mb-6 text-slate-800 dark:text-white leading-snug">Subject Here</h2>
                
                <div class="bg-gray-50 dark:bg-slate-800/50 p-4 rounded-xl border border-gray-100 dark:border-slate-700 font-mono text-sm leading-relaxed text-slate-600 dark:text-slate-300 overflow-x-auto" id="read-body">
                    Body Content...
                </div>
            </div>
        </div>
    </div>

    <div id="history-overlay" class="fixed inset-0 z-40 hidden bg-black/50 backdrop-blur-sm transition-opacity opacity-0" onclick="closeHistory()"></div>
    <div id="history-panel" class="fixed bottom-0 left-0 w-full bg-white dark:bg-slate-800 rounded-t-3xl z-50 p-6 shadow-2xl transform translate-y-full transition-transform duration-300 max-h-[70vh] flex flex-col">
        <div class="w-12 h-1.5 bg-gray-300 dark:bg-slate-600 rounded-full mx-auto mb-6"></div>
        <div class="flex justify-between items-center mb-4">
            <h3 class="text-lg font-bold">Switch Account</h3>
            <button onclick="clearHistory()" class="text-red-500 text-xs font-bold uppercase">Clear All</button>
        </div>
        <div id="history-list" class="overflow-y-auto space-y-2 flex-1 pr-1 pb-4"></div>
    </div>

    <div id="toast" class="fixed top-5 left-1/2 -translate-x-1/2 bg-slate-800 text-white px-6 py-3 rounded-full shadow-2xl z-[60] flex items-center gap-3 transition-all duration-300 opacity-0 -translate-y-10 pointer-events-none">
        <i class="fa-solid fa-circle-check text-green-400"></i> <span id="toast-msg">OK</span>
    </div>

    <script>
        const DOMAIN = "buffaloadmin.online";
        let currentEmail = "";
        let emailHistory = JSON.parse(localStorage.getItem("buffalo_history_v4")) || [];
        // Local cache for message counts
        let msgCounts = JSON.parse(localStorage.getItem("buffalo_counts")) || {};

        function init() {
            if (localStorage.getItem('theme') === 'light') document.documentElement.classList.remove('dark');
            
            const saved = localStorage.getItem("buffalo_active");
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
            localStorage.setItem("buffalo_active", email);
            document.getElementById("current-email").innerText = email;
            
            // Reset Inbox View
            document.getElementById("inbox").innerHTML = `
                <div class="text-center py-20 animate-pulse">
                    <div class="w-16 h-16 bg-blue-100 dark:bg-blue-900/30 rounded-full flex items-center justify-center mx-auto mb-4">
                        <i class="fa-solid fa-satellite-dish text-2xl text-blue-500"></i>
                    </div>
                    <p class="text-sm text-gray-500">Connecting...</p>
                </div>`;
            document.getElementById("msg-count").innerText = "0";

            if (saveHist) {
                if (!emailHistory.includes(email)) emailHistory.unshift(email);
                if (emailHistory.length > 15) emailHistory.pop();
                localStorage.setItem("buffalo_history_v4", JSON.stringify(emailHistory));
            }
            
            closeHistory();
            fetchEmails(false);
        }

        async function fetchEmails(silent = false) {
            if (!currentEmail) return;
            const icon = document.getElementById("refresh-icon");
            if(!silent) icon.classList.add("fa-spin");

            try {
                const res = await fetch(`/api/emails?address=${currentEmail}`);
                const data = await res.json();
                
                // Update Count in UI & Cache
                document.getElementById("msg-count").innerText = data.length;
                msgCounts[currentEmail] = data.length;
                localStorage.setItem("buffalo_counts", JSON.stringify(msgCounts));
                updateHistoryBadges();

                const inbox = document.getElementById("inbox");
                if (data.length > 0) {
                    inbox.innerHTML = data.reverse().map((msg, index) => {
                        // Store full data in a hidden attribute to read later
                        const safeSender = msg.sender.replace(/'/g, "&apos;");
                        const safeSubject = msg.subject.replace(/'/g, "&apos;");
                        const safeBody = encodeURIComponent(msg.body); // Encode to pass safely
                        
                        // Preview Body
                        let preview = msg.body.substring(0, 60) + (msg.body.length > 60 ? "..." : "");
                        
                        return `
                        <div onclick="openReadModal('${safeSender}', '${safeSubject}', '${safeBody}', '${msg.timestamp}')" 
                            class="bg-white dark:bg-slate-800 p-4 rounded-2xl shadow-sm border border-gray-100 dark:border-slate-700 relative overflow-hidden group active:scale-[0.98] transition cursor-pointer">
                            <div class="flex justify-between items-start mb-1">
                                <div class="font-bold text-sm text-slate-800 dark:text-slate-100 truncate w-[70%]">${msg.sender}</div>
                                <span class="text-[10px] text-gray-400">${msg.timestamp}</span>
                            </div>
                            <div class="font-bold text-blue-600 dark:text-blue-400 text-sm mb-1 truncate">${msg.subject}</div>
                            <div class="text-xs text-gray-500 dark:text-slate-400 truncate">${preview}</div>
                        </div>`;
                    }).join("");
                } else if (!silent) {
                    inbox.innerHTML = '<div class="text-center py-10 opacity-40"><i class="fa-regular fa-envelope-open text-5xl mb-3"></i><p class="text-sm">No messages yet</p></div>';
                }
            } catch (e) { console.error(e); }
            
            if(!silent) setTimeout(() => icon.classList.remove("fa-spin"), 500);
        }

        // --- READ MODE ---
        function openReadModal(sender, subject, encodedBody, date) {
            const body = decodeURIComponent(encodedBody);
            
            document.getElementById("read-sender").innerText = sender;
            document.getElementById("read-avatar").innerText = sender.charAt(0).toUpperCase();
            document.getElementById("read-subject").innerText = subject;
            document.getElementById("read-date").innerText = date;
            
            // Smart OTP Highlight for Read View
            let formattedBody = body.replace(/</g, "&lt;");
            formattedBody = formattedBody.replace(/\\b\\d{4,8}\\b/g, match => `<span class="otp-badge" onclick="copyText('${match}')">${match}</span>`);
            formattedBody = formattedBody.replace(/\\n/g, "<br>");
            
            document.getElementById("read-body").innerHTML = formattedBody;

            const modal = document.getElementById("read-modal");
            const box = document.getElementById("read-content-box");
            modal.classList.remove("hidden");
            // Animation
            setTimeout(() => { box.classList.remove("translate-y-full"); }, 10);
        }

        function closeReadModal() {
            const box = document.getElementById("read-content-box");
            box.classList.add("translate-y-full");
            setTimeout(() => { document.getElementById("read-modal").classList.add("hidden"); }, 300);
        }

        // --- HISTORY UI ---
        function openHistory() {
            updateHistoryBadges(); // Refresh counts before showing
            const list = document.getElementById("history-list");
            
            if (emailHistory.length > 0) {
                list.innerHTML = emailHistory.map(email => {
                    const isActive = email === currentEmail;
                    const count = msgCounts[email] || 0;
                    
                    return `
                    <div onclick="switchAccount('${email}')" class="p-3 rounded-xl flex items-center justify-between cursor-pointer transition mb-2 ${isActive ? 'bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800' : 'bg-gray-50 dark:bg-slate-700/50'}">
                        <div class="flex items-center gap-3 overflow-hidden">
                            <div class="w-8 h-8 rounded-full ${isActive ? 'bg-blue-500' : 'bg-gray-300 dark:bg-slate-600'} flex items-center justify-center text-white font-bold text-xs">
                                ${email.charAt(0).toUpperCase()}
                            </div>
                            <div class="flex flex-col overflow-hidden">
                                <span class="font-mono text-xs font-bold truncate ${isActive ? 'text-blue-600 dark:text-blue-400' : 'text-gray-700 dark:text-gray-300'}">${email}</span>
                            </div>
                        </div>
                        <div class="flex items-center gap-2">
                            ${count > 0 ? `<span class="bg-red-500 text-white text-[10px] font-bold px-2 py-0.5 rounded-full shadow-sm">${count} New</span>` : ''}
                            ${isActive ? '<i class="fa-solid fa-check-circle text-blue-500"></i>' : ''}
                        </div>
                    </div>`;
                }).join('');
            } else {
                list.innerHTML = '<p class="text-center text-gray-400 text-sm mt-4">No history yet</p>';
            }

            document.getElementById("history-overlay").classList.remove("hidden");
            setTimeout(() => {
                document.getElementById("history-overlay").classList.remove("opacity-0");
                document.getElementById("history-panel").classList.remove("translate-y-full");
            }, 10);
        }

        function closeHistory() {
            document.getElementById("history-overlay").classList.add("opacity-0");
            document.getElementById("history-panel").classList.add("translate-y-full");
            setTimeout(() => { document.getElementById("history-overlay").classList.add("hidden"); }, 300);
        }

        function updateHistoryBadges() {
            // Calculate total unread (simple sum of counts)
            let total = 0;
            emailHistory.forEach(e => { if(msgCounts[e]) total += msgCounts[e]; });
            
            const badge = document.getElementById("total-badge");
            if(total > 0) {
                badge.innerText = total > 9 ? '9+' : total;
                badge.classList.remove("hidden");
            } else {
                badge.classList.add("hidden");
            }
        }
        
        function clearHistory() {
            if(confirm("Clear history?")) {
                emailHistory = []; msgCounts = {};
                localStorage.removeItem("buffalo_history_v4");
                localStorage.removeItem("buffalo_counts");
                closeHistory();
            }
        }

        function manualRefresh() { fetchEmails(); }
        function toggleTheme() {
            const html = document.documentElement;
            if (html.classList.contains('dark')) { html.classList.remove('dark'); localStorage.setItem('theme', 'light'); } 
            else { html.classList.add('dark'); localStorage.setItem('theme', 'dark'); }
        }
        function copyEmail() { navigator.clipboard.writeText(currentEmail); showToast("Copied!"); }
        function copyText(txt) { navigator.clipboard.writeText(txt); showToast("Code Copied!"); }
        function showToast(msg) {
            const toast = document.getElementById("toast"); document.getElementById("toast-msg").innerText = msg;
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
        # လက်ခံရရှိချိန် (Time) ထည့်ပေးခြင်း
        now = datetime.now().strftime("%H:%M")
        data['timestamp'] = now
        
        recipient = data.get('recipient')
        
        # User တစ်ယောက်ချင်းစီအတွက် သီးသန့် Inbox ဆောက်ပေးခြင်း
        if recipient not in user_inboxes:
            user_inboxes[recipient] = []
        
        user_inboxes[recipient].append(data)
        
        # Memory များမသွားအောင် ထိန်းခြင်း
        if len(user_inboxes[recipient]) > 50:
            user_inboxes[recipient
