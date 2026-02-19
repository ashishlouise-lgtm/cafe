
        import os, json, threading, urllib.parse
from http.server import BaseHTTPRequestHandler, HTTPServer
from telegram import ReplyKeyboardMarkup, KeyboardButton, WebAppInfo, Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

# --- CONFIG ---
MY_PHONE = "918078619566" 
TOKEN = os.getenv("TOKEN")
WEB_LINK = "https://ashishlouise-lgtm.github.io/cafe/" 
DB_FILE = "database.json"

# --- JSON DATABASE LOGIC ---
def load_db():
    if not os.path.exists(DB_FILE): return {}
    with open(DB_FILE, "r") as f:
        try: return json.load(f)
        except: return {}

def save_db(data):
    with open(DB_FILE, "w") as f: json.dump(data, f, indent=4)

# --- BOT LOGIC ---
user_data = {}

async def start(update, context):
    uid = str(update.effective_user.id)
    user_data[uid] = {"cart": [], "total": 0, "state": "ORDERING"}
    web_app = WebAppInfo(url=WEB_LINK)
    kb = [[KeyboardButton("📱 Open Stylish Menu", web_app=web_app)]]
    await update.message.reply_text("✨ *Welcome to Crushescafe!* ✨\nNiche button se menu kholein:", 
                                   reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True), parse_mode='Markdown')

async def handle_web_app_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    data = json.loads(update.effective_message.web_app_data.data)
    user_data[uid] = {"cart": data['items'], "total": data['total'], "state": "ASK_NAME"}
    kb = [[InlineKeyboardButton("❌ Cancel Order", callback_data="cancel_order")]]
    await update.message.reply_text(f"🧾 *Order Received!* Total: ₹{data['total']}\n\nAb apna **Naam** likhein:", 
                                   reply_markup=InlineKeyboardMarkup(kb), parse_mode='Markdown')

async def handle_text(update, context):
    uid = str(update.message.from_user.id)
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
        db = load_db()
        visit_count = db.get(uid, {}).get("visits", 0) + 1
        name, total, items = user_data[uid]["name"], user_data[uid]["total"], ", ".join(user_data[uid]["cart"])
        
        # Loyalty Discount Alert
        discount_tag = "\n\n🌟 *LOYALTY ALERT: GIVE DISCOUNT!*" if visit_count >= 20 else ""
        
        wa_text = f"🔥 *NEW ORDER* 🔥\n👤 Name: {name}\n💰 Total: ₹{total}\n📍 Address: {txt}\n📊 Visits: {visit_count}{discount_tag}"
        wa_link = f"https://wa.me/{MY_PHONE}?text={urllib.parse.quote(wa_text)}"
        
        kb = [[InlineKeyboardButton("💬 Confirm on WhatsApp", url=wa_link)],
              [InlineKeyboardButton("✅ Order Sent! (Done)", callback_data="clear_order")]]
        
        await update.message.reply_text(f"🎉 *Order taiyaar hai {name}!*\nAapki visit count: {visit_count}/20\nWhatsApp par bhej dein:", 
                                       reply_markup=InlineKeyboardMarkup(kb), parse_mode='Markdown')

async def handle_callback(update, context):
    query = update.callback_query
    uid = str(query.from_user.id)
    await query.answer()
    
    if query.data == "clear_order":
        db = load_db()
        if uid not in db: db[uid] = {"name": user_data[uid].get("name", "New"), "visits": 0}
        db[uid]["visits"] += 1
        db[uid]["name"] = user_data[uid].get("name", db[uid]["name"])
        save_db(db)
        await query.edit_message_text(f"💖 *Shukriya {db[uid]['name']}!* Visit #{db[uid]['visits']} register ho gayi. 🙏")
        if uid in user_data: del user_data[uid]
    elif query.data == "cancel_order":
        if uid in user_data: del user_data[uid]
        await query.edit_message_text("❌ *Order Cancelled!* Phir milte hain.")

# --- SERVER & RUN ---
def main():
    threading.Thread(target=lambda: HTTPServer(('0.0.0.0', int(os.environ.get("PORT", 10000))), BaseHTTPRequestHandler).serve_forever(), daemon=True).start()
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, handle_web_app_data))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.run_polling(drop_pending_updates=True)

if __name__ == '__main__': main()
