     import os
import json
import threading
import urllib.parse
from http.server import BaseHTTPRequestHandler, HTTPServer
from telegram import ReplyKeyboardMarkup, KeyboardButton, WebAppInfo, Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# --- CONFIG ---
MY_PHONE = "918078619566" 
TOKEN = os.getenv("TOKEN")
WEB_LINK = "https://ashishlouise-lgtm.github.io/cafe/" 

class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200); self.end_headers()
        self.wfile.write(b"Bot is Zinda!")

def run_dummy_server():
    server = HTTPServer(('0.0.0.0', int(os.environ.get("PORT", 10000))), HealthCheckHandler)
    server.serve_forever()

user_data = {}

async def start(update, context):
    uid = update.effective_user.id
    user_data[uid] = {"cart": [], "total": 0, "state": "ORDERING"}
    web_app = WebAppInfo(url=WEB_LINK)
    kb = [[KeyboardButton("📱 Open Stylish Menu", web_app=web_app)]]
    await update.message.reply_text(
        "✨ *Welcome to Crushescafe!* ✨\n\nNiche keyboard mein jo 'Open Menu' button aaya hai, use dabakar order karein:",
        reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True),
        parse_mode='Markdown'
    )

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
        await update.message.reply_text("📍 Ab apna **Full Address** likhein:")

    elif state == "ASK_ADDRESS":
        name = user_data[uid]["name"]
        total = user_data[uid]["total"]
        items_str = ", ".join(user_data[uid]["cart"])
        
        # WhatsApp Message taiyaar karna
        wa_text = f"🔥 *NEW ORDER - Crushescafe* 🔥\n\n👤 *Name:* {name}\n🍔 *Items:* {items_str}\n💰 *Total:* ₹{total}\n📍 *Address:* {txt}"
        wa_link = f"https://wa.me/{MY_PHONE}?text={urllib.parse.quote(wa_text)}"
        
        # Customer ke liye pyara sa success message
        success_msg = (
            f"🎉 *Shabaash {name}! Aapka Order Book Ho Gaya Hai!* 🥳\n\n"
            f"🍔 *Items:* {items_str}\n"
            f"💰 *Bill:* ₹{total}\n"
            f"📍 *Delivery Address:* {txt}\n\n"
            f"Niche diye gaye button par click karke WhatsApp par confirm kar dein! 👇"
        )
        
        kb = [[InlineKeyboardButton("✅ Confirm on WhatsApp", url=wa_link)]]
        
        await update.message.reply_text(success_msg, reply_markup=InlineKeyboardMarkup(kb), parse_mode='Markdown')
        del user_data[uid]

def main():
    threading.Thread(target=run_dummy_server, daemon=True).start()
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, handle_web_app_data))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    main()   
