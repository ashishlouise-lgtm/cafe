import os, json, threading, urllib.parse
from http.server import BaseHTTPRequestHandler, HTTPServer
from telegram import ReplyKeyboardMarkup, KeyboardButton, WebAppInfo, Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

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
    await update.message.reply_text("✨ *Welcome to Crushescafe!* ✨\nNiche button se menu kholein:", 
                                   reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True), parse_mode='Markdown')

async def handle_web_app_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    data = json.loads(update.effective_message.web_app_data.data)
    user_data[uid] = {"cart": data['items'], "total": data['total'], "state": "ASK_NAME"}
    kb = [[InlineKeyboardButton("❌ Cancel Order", callback_data="cancel_order")]]
    await update.message.reply_text(f"🧾 *Order Received!* Total: ₹{data['total']}\n\nAb apna **Naam** likhein:", 
                                   reply_markup=InlineKeyboardMarkup(kb), parse_mode='Markdown')

async def handle_text(update, context):
    uid = update.message.from_user.id
    txt = update.message.text
    if txt.lower() in ["hi", "hello", "start"]:
        await start(update, context); return
    if uid not in user_data: return
    state = user_data[uid].get("state")
    cancel_kb = [[InlineKeyboardButton("❌ Cancel Order", callback_data="cancel_order")]]

    if state == "ASK_NAME":
        user_data[uid]["name"] = txt
        user_data[uid]["state"] = "ASK_ADDRESS"
        await update.message.reply_text(f"📍 Shabaash {txt}! Ab apna **Address** likhein:", reply_markup=InlineKeyboardMarkup(cancel_kb))

    elif state == "ASK_ADDRESS":
        name, total, items = user_data[uid]["name"], user_data[uid]["total"], ", ".join(user_data[uid]["cart"])
        wa_text = f"🔥 *NEW ORDER* 🔥\n👤 Name: {name}\n🍔 Items: {items}\n💰 Total: ₹{total}\n📍 Address: {txt}"
        wa_link = f"https://wa.me/{MY_PHONE}?text={urllib.parse.quote(wa_text)}"
        kb = [[InlineKeyboardButton("💬 Confirm on WhatsApp", url=wa_link)],
              [InlineKeyboardButton("✅ Order Sent! Clear Chat", callback_data="clear_order")]]
        await update.message.reply_text("🎉 *Aapka form bhar gaya hai!* Niche button se WhatsApp par bhej dein:", 
                                       reply_markup=InlineKeyboardMarkup(kb), parse_mode='Markdown')

async def handle_callback(update, context):
    query = update.callback_query
    await query.answer()
    if query.data == "clear_order":
        await query.edit_message_text("💖 *Order Booked!* Shukriya! 🙏✨")
    elif query.data == "cancel_order":
        if query.from_user.id in user_data: del user_data[query.from_user.id]
        await query.edit_message_text("❌ *Order Cancelled!*")

def main():
    threading.Thread(target=run_dummy_server, daemon=True).start()
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, handle_web_app_data))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.run_polling(drop_pending_updates=True)

if __name__ == '__main__': main()
