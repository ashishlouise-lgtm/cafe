import os
import json
import threading
import urllib.parse
from http.server import BaseHTTPRequestHandler, HTTPServer
from telegram import ReplyKeyboardMarkup, KeyboardButton, WebAppInfo, Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

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
        
        wa_text = f"🔥 *NEW ORDER - Crushescafe* 🔥\n\n👤 *Name:* {name}\n🍔 *Items:* {items_str}\n💰 *Total:* ₹{total}\n📍 *Address:* {txt}"
        wa_link = f"https://wa.me/{MY_PHONE}?text={urllib.parse.quote(wa_text)}"
        
        # WhatsApp button aur ek 'Done' button taaki hum ise baad mein hata sakein
        kb = [
            [InlineKeyboardButton("💬 Confirm on WhatsApp", url=wa_link)],
            [InlineKeyboardButton("✅ Order Sent! Clear Chat", callback_data="clear_order")]
        ]
        
        await update.message.reply_text(
            f"🎉 *Shabaash {name}!* Aapka form bhar gaya hai.\n\n"
            f"1️⃣ Pehle upar wale button se WhatsApp par order bhej dein.\n"
            f"2️⃣ Phir wapas aakar 'Order Sent' dabayein.",
            reply_markup=InlineKeyboardMarkup(kb),
            parse_mode='Markdown'
        )

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """WhatsApp se wapas aane par message chamkane ke liye"""
    query = update.callback_query
    await query.answer()
    
    if query.data == "clear_order":
        # Purana WhatsApp button wala message edit karke hata dega
        await query.edit_message_text(
            "💖 *Shukriya! Aapka order Crushescafe par book ho gaya hai.*\n\n"
            "Hum jald hi aapki delivery taiyaar karenge. Agle order ke liye phir se 'Hi' likhein! 🙏✨",
            parse_mode='Markdown'
        )

def main():
    threading.Thread(target=run_dummy_server, daemon=True).start()
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_callback)) # Button click handle karne ke liye
    app.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, handle_web_app_data))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    main()
