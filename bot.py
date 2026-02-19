import os, json, base64, requests, threading, urllib.parse
from http.server import BaseHTTPRequestHandler, HTTPServer
from telegram import ReplyKeyboardMarkup, KeyboardButton, WebAppInfo, Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

# --- CONFIG ---
MY_PHONE = "918078619566" #
TOKEN = os.getenv("TOKEN")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN") 
REPO_NAME = "ashishlouise-lgtm/cafe" #
DB_FILE = "database.json"

# --- GITHUB DATABASE LOGIC ---
def get_github_data():
    url = f"https://api.github.com/repos/{REPO_NAME}/contents/{DB_FILE}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    r = requests.get(url, headers=headers)
    if r.status_code == 200:
        content = r.json()
        db = json.loads(base64.b64decode(content['content']).decode())
        return db, content['sha']
    return {}, None

def update_github_db(uid, name):
    try:
        db, sha = get_github_data()
        uid_str = str(uid)
        
        if uid_str not in db:
            db[uid_str] = {"name": name, "visits": 0}
        
        db[uid_str]["visits"] += 1
        db[uid_str]["name"] = name
        
        # GitHub par wapas bhej rahe hain
        new_content = base64.b64encode(json.dumps(db, indent=4).encode()).decode()
        url = f"https://api.github.com/repos/{REPO_NAME}/contents/{DB_FILE}"
        headers = {"Authorization": f"token {GITHUB_TOKEN}"}
        payload = {
            "message": f"Update visits for {name}",
            "content": new_content,
            "sha": sha
        }
        requests.put(url, json=payload, headers=headers)
        return db[uid_str]["visits"]
    except Exception as e:
        print(f"GitHub Error: {e}")
        return 0

# --- BOT LOGIC ---
user_data = {}

async def start(update, context):
    uid = update.effective_user.id
    user_data[uid] = {"cart": [], "total": 0, "state": "ORDERING"}
    web_app = WebAppInfo(url=f"https://ashishlouise-lgtm.github.io/cafe/") #
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
        await update.message.reply_text(f"📍 Shabaash {txt}! Ab apna **Full Address** likhein:")

    elif state == "ASK_ADDRESS":
        name = user_data[uid]["name"]
        total = user_data[uid]["total"]
        # GitHub se visit count temporary check karein (Sirf UI ke liye)
        wa_text = f"🔥 *NEW ORDER* 🔥\n👤 Name: {name}\n💰 Total: ₹{total}\n📍 Address: {txt}"
        wa_link = f"https://wa.me/{MY_PHONE}?text={urllib.parse.quote(wa_text)}"
        
        kb = [[InlineKeyboardButton("💬 Confirm on WhatsApp", url=wa_link)],
              [InlineKeyboardButton("✅ Order Sent! (Save Visit)", callback_data="clear_order")]]
        
        await update.message.reply_text(f"🎉 *Order taiyaar hai {name}!*\n\nWhatsApp par bhej kar 'Order Sent' dabayein 👇", 
                                       reply_markup=InlineKeyboardMarkup(kb), parse_mode='Markdown')

async def handle_callback(update, context):
    query = update.callback_query
    uid = query.from_user.id
    await query.answer()
    
    if query.data == "clear_order":
        name = user_data[uid].get("name", "Customer")
        # GitHub API call to save visit
        visit_no = update_github_db(uid, name)
        
        discount_msg = "\n\n🎁 *20 Visits Done! Discount Milega!*" if visit_no >= 20 else ""
        await query.edit_message_text(f"💖 *Shukriya {name}!*\nAapki {visit_no}th visit register ho gayi. 🙏{discount_msg}")
        if uid in user_data: del user_data[uid]

# --- HEALTH CHECK SERVER ---
def main():
    threading.Thread(target=lambda: HTTPServer(('0.0.0.0', int(os.environ.get("PORT", 10000))), BaseHTTPRequestHandler).serve_forever(), daemon=True).start()
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, handle_web_app_data))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.run_polling(drop_pending_updates=True)

if __name__ == '__main__': main()
