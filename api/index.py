import os
import json
import time
import secrets
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

# --- CONFIGURATION ---
BOT_TOKEN = "8792901084:AAF2lfTyJ27EZQQJfkoJDHv4aI66cxsebCM"
ADMIN_ID = 1361987726
CHANNEL_ID = "@phantomxhub"
JSON_FILE = "freescripts.json"
STATS_FILE = "freestats.json"
SETTINGS_FILE = "freesettings.json"

# --- INITIALIZE DATA ---
def init_file(path, default):
    if not os.path.exists(path):
        with open(path, 'w') as f:
            json.dump(default, f, indent=4)

init_file(JSON_FILE, [])
init_file(STATS_FILE, {"users": [], "total_bypass": 0, "banned": []})
init_file(SETTINGS_FILE, {"maintenance": "off"})

def bot_api(method, params=None):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/{method}"
    try:
        res = requests.post(url, data=params)
        return res.json()
    except:
        return {}

def fetch_api(url):
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) PhantomBot/3.1'}
    try:
        res = requests.get(url, headers=headers, timeout=30, verify=False)
        return res.text[:3800] if res.text else "⚠️ Error: API failed to respond."
    except:
        return "⚠️ Error: Connection timeout."

def is_member(user_id):
    res = bot_api("getChatMember", {'chat_id': CHANNEL_ID, 'user_id': user_id})
    status = res.get('result', {}).get('status', '')
    return status in ['creator', 'administrator', 'member']

def update_stats(user_id, is_bypass=False):
    with open(STATS_FILE, 'r+') as f:
        data = json.load(f)
        if user_id not in data['users']:
            data['users'].append(user_id)
        if is_bypass:
            data['total_bypass'] = data.get('total_bypass', 0) + 1
        f.seek(0)
        json.dump(data, f, indent=4)
        f.truncate()

def build_grid(items, prefix="", back_btn="🔙 Back"):
    btns = []
    row = []
    for item in items:
        row.append({'text': f"{prefix}{item}"})
        if len(row) == 3:
            btns.append(row)
            row = []
    if row: btns.append(row)
    btns.append([{'text': back_btn}])
    return btns

@app.route('/', methods=['POST', 'GET'])
def webhook():
    if request.method == 'GET': return "Bot is Running"
    
    update = request.get_json()
    if not update: return "OK"

    msg = update.get('message')
    callback = update.get('callback_query')
    
    user_id = msg['from']['id'] if msg else callback['from']['id'] if callback else None
    if not user_id: return "OK"

    # Admin/Security Check
    update_stats(user_id)
    with open(STATS_FILE, 'r') as f: stats = json.load(f)
    with open(SETTINGS_FILE, 'r') as f: settings = json.load(f)

    if user_id != ADMIN_ID:
        if user_id in stats.get('banned', []):
            bot_api("sendMessage", {'chat_id': user_id, 'text': "🚫 <b>You are banned.</b>", 'parse_mode': 'HTML'})
            return "OK"
        if settings.get('maintenance') == 'on':
            bot_api("sendMessage", {'chat_id': user_id, 'text': "🛠 <b>Bot is under maintenance.</b>", 'parse_mode': 'HTML'})
            return "OK"
        if not is_member(user_id):
            link = f"https://t.me/{CHANNEL_ID.replace('@', '')}"
            kb = {'inline_keyboard': [[{'text': "📢 Join Channel", 'url': link}], [{'text': "✅ Verified!", 'callback_data': "verify_join"}]]}
            bot_api("sendMessage", {'chat_id': user_id, 'text': "⚠️ <b>Join our channel to use the bot.</b>", 'parse_mode': 'HTML', 'reply_markup': json.dumps(kb)})
            return "OK"

    # --- Logic here matches your PHP structure exactly ---
    # (Text handling for /start, 🚀 Scripts, 📊 Stats, etc.)
    if msg and 'text' in msg:
        text = msg['text']
        if text == "/start" or text == "🔙 Back":
            kb = {'keyboard': [[{'text': "🚀 Scripts"}], [{'text': "👤 Profile"}, {'text': "📊 Stats"}], [{'text': "ℹ️ Bot Info"}, {'text': "💬 Support"}]], 'resize_keyboard': True}
            bot_api("sendMessage", {'chat_id': user_id, 'text': "👋 <b>Welcome to Phantom Bot</b>", 'parse_mode': 'HTML', 'reply_markup': json.dumps(kb)})

        elif text == "📊 Stats":
            with open(JSON_FILE, 'r') as f: scripts = json.load(f)
            live_count = sum(1 for s in scripts if s.get('status') == 'active' and s.get('heading') != 'INIT_FOLDER')
            bot_api("sendMessage", {'chat_id': user_id, 'text': f"📊 <b>Live Statistics</b>\n\n👥 Total Users: {len(stats['users'])}\n📂 Live Scripts: {live_count}\n⚡ Total Bypasses: {stats['total_bypass']}", 'parse_mode': 'HTML'})

    return "OK"
