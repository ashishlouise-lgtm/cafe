import os, json, base64, requests, threading, urllib.parse, logging
from http.server import BaseHTTPRequestHandler, HTTPServer
from telegram import ReplyKeyboardMarkup, KeyboardButton, WebAppInfo, Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

# Logging setup taaki errors dikhein
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# --- CONFIG ---
MY_PHONE = "918078619566" #
TOKEN = os.getenv("TOKEN") # Render Env se aayega
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN") # Render Env se aayega
REPO_NAME = "ashishlouise-lgtm/cafe" #
DB_FILE = "database.json" #

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
        
        # GitHub par data wapas bhej rahe hain
        new_content = base64.b64encode(json.dumps(db, indent=4).encode()).decode()
        url = f"https://api.github.com/repos/{REPO_NAME}/contents/{DB_FILE}"
        headers = {"Authorization": f"token {GITHUB_TOKEN}"}
        payload = {
            "message": f"Update visits for {name}",
            "content": new_content,
            "sha": sha
        }
        r = requests.put(url, json=payload, headers=headers)
        if r.status_code == 200 or r.status_code == 201:
            logging.info(f"GitHub Updated: {name} now has {db[uid_str]['visits']} visits.")
            return db[uid_str]["visits"]
    except Exception as e:
        logging.error(f"GitHub Error: {e}")
    return 0

# --- BOT LOGIC ---
user_data = {}

async def start(update, context):
    uid = update.effective_user.id
    user_data[uid] = {"cart": [], "total": 0, "state": "ORDERING"}
    web_app = WebAppInfo(url=f"https://ashishlouise-lgtm.github.io/cafe/") #
    kb = [[KeyboardButton("📱 Open Stylish Menu", web_app=web_app)]]
    await update.message.reply_text(
        "✨ *Welcome to Crushescafe!* ✨\n\nNiche button se menu kholein aur order karein:", 
        reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True), 
        parse_mode='Markdown'
    )

async def handle_web_app_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    data = json.loads(update.effective_message.web_app_data.data)
    user_data[uid] = {"cart": data['items'], "total": data['total'], "state": "ASK_NAME"}
    
    kb = [[InlineKeyboardButton("❌ Cancel Order", callback_data="cancel_order")]]
    await update.message.reply_text(
        f"🧾 *Order Received!* Total: ₹{data['total']}\n\nAb apna **Naam** likhein:", 
        reply_markup=InlineKeyboardMarkup(kb),
        parse_mode='Markdown'
    )

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
        items_str = ", ".join(user_data[uid]["cart"])
        
        wa_text = f"🔥 *NEW ORDER - Crushescafe* 🔥\n\n👤 *Name:* {name}\n🍔 *Items:* {items_str}\n💰 *Total:* ₹{total}\n📍 *Address:* {txt}"
        wa_link = f"https://wa.me/{MY_PHONE}?text={urllib.parse.quote(wa_text)}"
        
        kb = [[InlineKeyboardButton("💬 Confirm on WhatsApp", url=wa_link)],
              [InlineKeyboardButton("✅ Order Sent! (Save Visit)", callback_data="clear_order")]]
        
        await update.message.reply_text(
            f"🎉 *Order taiyaar hai {name}!*\n\nWhatsApp par bhej kar niche 'Order Sent' dabayein 👇", 
            reply_markup=InlineKeyboardMarkup(kb), 
            parse_mode='Markdown'
        )

async def handle_callback(update, context):
    query = update.callback_query
    uid = query.from_user.id
    await query.answer()
    
    if query.data == "clear_order":
        if uid in user_data:
            name = user_data[uid].get("name", "Grahak")
            # GitHub par visit save karein
            visit_no = update_github_db(uid, name)
            
            msg = f"💖 *Shukriya {name}!* \n\nAapki {visit_no}th visit register ho gayi hai. 🙏✨"
            if visit_no >= 20:
                msg += "\n\n🎁 *LOYALTY REWARD:* Agli baar discount milega!"
            
            await query.edit_message_text(msg, parse_mode='Markdown')
            del user_data[uid]
        else:
            await query.edit_message_text("💖 *Thank You!* Aapka order register ho chuka hai.")

    elif query.data == "cancel_order":
        if uid in user_data: del user_data[uid]
        await query.edit_message_text("❌ *Order Cancelled!* \n\n'Hi' likhkar fir se shuru karein.")

# --- HEALTH CHECK SERVER ---
def main():
    threading.Thread(target=lambda: HTTPServer(('0.0.0.0', int(os.environ.get("PORT", 10000))), BaseHTTPRequestHandler).serve_forever(), daemon=True).start()
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, handle_web_app_data))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    main()
