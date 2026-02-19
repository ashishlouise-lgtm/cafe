    
    import os, json, base64, requests, threading, urllib.parse, logging
from http.server import BaseHTTPRequestHandler, HTTPServer
from telegram import ReplyKeyboardMarkup, KeyboardButton, WebAppInfo, Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

# --- LOGGING ---
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# --- CONFIG ---
MY_PHONE = "918078619566"
TOKEN = os.getenv("TOKEN") 
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN") 
REPO_NAME = "ashishlouise-lgtm/cafe"
DB_FILE = "database.json" 
PORT = int(os.environ.get("PORT", 10000))

# --- GITHUB JUGAD ---
def update_github_db(uid, name):
    try:
        url = f"https://api.github.com/repos/{REPO_NAME}/contents/{DB_FILE}"
        headers = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
        r = requests.get(url, headers=headers)
        if r.status_code == 200:
            content = r.json()
            sha = content['sha']
            db = json.loads(base64.b64decode(content['content']).decode('utf-8'))
            uid_str = str(uid)
            if uid_str not in db: db[uid_str] = {"name": name, "visits": 0}
            db[uid_str]["visits"] += 1
            db[uid_str]["name"] = name
            new_content = base64.b64encode(json.dumps(db, indent=4).encode('utf-8')).decode('utf-8')
            payload = {"message": f"Visit for {name}", "content": new_content, "sha": sha}
            requests.put(url, json=payload, headers=headers)
            return db[uid_str]["visits"]
    except Exception as e:
        logger.error(f"GitHub Error: {e}")
    return 0

# --- BOT LOGIC ---
user_data = {}

async def start(update, context):
    uid = update.effective_user.id
    user_data[uid] = {"state": "ORDERING"}
    web_app = WebAppInfo(url=f"https://ashishlouise-lgtm.github.io/cafe/")
    kb = [[KeyboardButton("📱 Open Stylish Menu", web_app=web_app)]]
    await update.message.reply_text("✨ *Crushescafe* ✨\nMenu kholein:", reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True), parse_mode='Markdown')

async def handle_text(update, context):
    uid = update.message.from_user.id
    txt = update.message.text
    if txt.lower() == "/start": return
    if uid not in user_data: return
    state = user_data[uid].get("state")
    if state == "ASK_NAME":
        user_data[uid]["name"], user_data[uid]["state"] = txt, "ASK_ADDRESS"
        await update.message.reply_text(f"📍 {txt}, ab apna **Address** likhein:")
    elif state == "ASK_ADDRESS":
        name, total = user_data[uid]["name"], user_data[uid]["total"]
        wa_link = f"https://wa.me/{MY_PHONE}?text={urllib.parse.quote(f'ORDER: {name} Total: {total} Addr: {txt}')}"
        kb = [[InlineKeyboardButton("💬 WhatsApp", url=wa_link)], [InlineKeyboardButton("✅ Order Sent", callback_data="clear_order")]]
        await update.message.reply_text("🎉 Confirm karein!", reply_markup=InlineKeyboardMarkup(kb), parse_mode='Markdown')

async def handle_callback(update, context):
    query = update.callback_query
    uid = query.from_user.id
    await query.answer()
    if query.data == "clear_order" and uid in user_data:
        name = user_data[uid].get("name", "Grahak")
        visit_no = update_github_db(uid, name)
        await query.edit_message_text(f"💖 *Shukriya {name}!* Visit #{visit_no} saved. 🙏", parse_mode='Markdown')
        del user_data[uid]

# --- RENDER HEALTH CHECK ---
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is alive")

def main():
    threading.Thread(target=lambda: HTTPServer(('0.0.0.0', PORT), HealthCheckHandler).serve_forever(), daemon=True).start()
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.run_polling(drop_pending_updates=True)

if __name__ == '__main__': main()
