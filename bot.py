import os, json, base64, requests, threading, urllib.parse, logging
from http.server import BaseHTTPRequestHandler, HTTPServer
from telegram import ReplyKeyboardMarkup, KeyboardButton, WebAppInfo, Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

# --- LOGGING SETUP ---
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# --- CONFIG ---
MY_PHONE = "918078619566"
TOKEN = os.getenv("TOKEN") 
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN") 
REPO_NAME = "ashishlouise-lgtm/cafe"
DB_FILE = "database.json" 

# --- GITHUB API MASTER JUGAD ---
def update_github_db(uid, name):
    try:
        url = f"https://api.github.com/repos/{REPO_NAME}/contents/{DB_FILE}"
        headers = {
            "Authorization": f"token {GITHUB_TOKEN}",
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "CrushescafeBot"
        }
        
        # 1. Get current file content & SHA
        r = requests.get(url, headers=headers)
        if r.status_code != 200:
            logger.error(f"❌ GitHub Get Error: {r.status_code} - Check Repo Name or Token")
            return 0
            
        content = r.json()
        sha = content['sha']
        db_raw = base64.b64decode(content['content']).decode('utf-8')
        db = json.loads(db_raw)
        
        # 2. Update visit count
        uid_str = str(uid)
        if uid_str not in db:
            db[uid_str] = {"name": name, "visits": 0}
        
        db[uid_str]["visits"] += 1
        db[uid_str]["name"] = name
        new_visit_count = db[uid_str]["visits"]
        
        # 3. Push back to GitHub
        updated_json = json.dumps(db, indent=4)
        encoded_content = base64.b64encode(updated_json.encode('utf-8')).decode('utf-8')
        
        payload = {
            "message": f"Order by {name} - Visit #{new_visit_count}",
            "content": encoded_content,
            "sha": sha
        }
        
        put_r = requests.put(url, json=payload, headers=headers)
        if put_r.status_code in [200, 201]:
            logger.info(f"✅ SUCCESS: GitHub updated for {name}")
            return new_visit_count
        else:
            logger.error(f"❌ GitHub Put Error: {put_r.status_code} - {put_r.text}")
            
    except Exception as e:
        logger.error(f"💥 Master Jugad Crash: {e}")
    return 0

# --- BOT LOGIC ---
user_data = {}

async def start(update, context):
    uid = update.effective_user.id
    user_data[uid] = {"state": "ORDERING"}
    web_app = WebAppInfo(url=f"https://ashishlouise-lgtm.github.io/cafe/")
    kb = [[KeyboardButton("📱 Open Stylish Menu", web_app=web_app)]]
    await update.message.reply_text("✨ *Welcome to Crushescafe!* ✨\n\nNiche button se menu kholein:", 
                                   reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True), parse_mode='Markdown')

async def handle_web_app_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    data = json.loads(update.effective_message.web_app_data.data)
    user_data[uid] = {"cart": data['items'], "total": data['total'], "state": "ASK_NAME"}
    await update.message.reply_text(f"🧾 *Order Received!* Total: ₹{data['total']}\n\nAb apna **Naam** likhein:", parse_mode='Markdown')

async def handle_text(update, context):
    uid = update.message.from_user.id
    txt = update.message.text
    if txt.lower() in ["hi", "hello", "start"]:
        await start(update, context); return
    if uid not in user_data: return
    
    state = user_data[uid].get("state")
    if state == "ASK_NAME":
        user_data[uid]["name"] = txt
        user_data[uid]["state"] = "ASK_ADDRESS"
        await update.message.reply_text(f"📍 Ok {txt}, ab apna **Address** likhein:")
    elif state == "ASK_ADDRESS":
        name, total = user_data[uid]["name"], user_data[uid]["total"]
        wa_text = f"🔥 *NEW ORDER* 🔥\n👤 Name: {name}\n💰 Total: ₹{total}\n📍 Address: {txt}"
        wa_link = f"https://wa.me/{MY_PHONE}?text={urllib.parse.quote(wa_text)}"
        kb = [[InlineKeyboardButton("💬 Confirm on WhatsApp", url=wa_link)],
              [InlineKeyboardButton("✅ Order Sent! (Save Visit)", callback_data="clear_order")]]
        await update.message.reply_text("🎉 *Confirm karein!*", reply_markup=InlineKeyboardMarkup(kb), parse_mode='Markdown')

async def handle_callback(update, context):
    query = update.callback_query
    uid = query.from_user.id
    await query.answer()
    
    if query.data == "clear_order":
        if uid in user_data:
            name = user_data[uid].get("name", "Grahak")
            visit_no = update_github_db(uid, name)
            
            if visit_no > 0:
                msg = f"💖 *Shukriya {name}!* \nAapki {visit_no}th visit register ho gayi. 🙏"
            else:
                msg = f"💖 *Order Sent!* \nShukriya Vijay bhai! Database mein thoda issue hai, par order humne note kar liya hai."
                
            await query.edit_message_text(msg, parse_mode='Markdown')
            del user_data[uid]

def main():
    threading.Thread(target=lambda: HTTPServer(('0.0.0.0', int(os.environ.get("PORT", 10000))), BaseHTTPRequestHandler).serve_forever(), daemon=True).start()
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, handle_web_app_data))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.run_polling(drop_pending_updates=True)

if __name__ == '__main__': main()
