import os
import json
import smtplib
import threading
import urllib.parse
from datetime import datetime
from http.server import BaseHTTPRequestHandler, HTTPServer
from email.message import EmailMessage
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, WebAppInfo
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

# --- CONFIG ---
# Apna sahi WhatsApp number yahan daalein
MY_PHONE = "919571646540" 
TOKEN = os.getenv("TOKEN")
MY_EMAIL = os.getenv("MY_EMAIL")
APP_PASSWORD = os.getenv("APP_PASSWORD")
# Apna GitHub Pages link yahan daalein
WEB_LINK = "https://ashishlouise-lgtm.github.io/cafe/"

class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200); self.end_headers()
        self.wfile.write(b"Bot and WebApp active!")
    def do_HEAD(self):
        self.send_response(200); self.end_headers()

def run_dummy_server():
    server = HTTPServer(('0.0.0.0', int(os.environ.get("PORT", 10000))), HealthCheckHandler)
    server.serve_forever()

user_data = {}

def send_email_now(name, address, cart, total):
    try:
        now = datetime.now().strftime("%d-%m-%Y %H:%M")
        items = "\n".join([f"• {item}" for item in cart])
        msg = EmailMessage()
        msg.set_content(f"Naya Order!\nWaqt: {now}\nCustomer: {name}\nAddress: {address}\n\nItems:\n{items}\n\nTotal: ₹{total}")
        msg['Subject'] = f"Cafe Order: {name}"; msg['From'] = MY_EMAIL; msg['To'] = MY_EMAIL
        with smtplib.SMTP_SSL('smtp.gmail.com', 465, timeout=10) as smtp:
            smtp.login(MY_EMAIL, APP_PASSWORD); smtp.send_message(msg)
    except: pass

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    user_data[uid] = {"cart": [], "total": 0, "state": "ORDERING"}
    
    # Stylish Menu Button jo Website kholega
    kb = [[InlineKeyboardButton("📱 Open Stylish Menu", web_app=WebAppInfo(url=WEB_LINK))],
          [InlineKeyboardButton("❌ Cancel Order", callback_data='cancel')]]
    
    await update.message.reply_text(
        '✨ *Welcome to Crushescafe!* ✨\n\nAb order karna aur bhi asan hai! Niche diye gaye *Menu* button par click karein aur apni pasandida items chunein.', 
        reply_markup=InlineKeyboardMarkup(kb), 
        parse_mode='Markdown'
    )

async def handle_web_app_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Website se aaye order data ko handle karta hai"""
    uid = update.effective_user.id
    # Website (index.html) se aaya data load karein
    data = json.loads(update.effective_message.web_app_data.data)
    
    user_data[uid] = {
        "cart": data['items'], 
        "total": data['total'], 
        "state": "ASK_NAME"
    }
    
    await update.message.reply_text(
        f"🧾 *Order Summary:*\nItems: {', '.join(data['items'])}\nTotal Bill: *₹{data['total']}*\n\nAb apna **Naam** likhein:", 
        parse_mode='Markdown'
    )

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query; await query.answer()
    uid = query.from_user.id
    
    if query.data == 'wa_done':
        await query.edit_message_text("💖 *Thank You!* \nAapka order jald hi taiyaar ho jayega. 🙏", parse_mode='Markdown')
        if uid in user_data: del user_data[uid]
        return

    if query.data == 'cancel':
        await query.edit_message_text("❌ Order cancelled. 'Hi' likhkar dobara shuru karein.")
        if uid in user_data: del user_data[uid]

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.message.from_user.id
    txt = update.message.text
    
    # Hi/Hello Start
    if txt.lower() in ["hi", "hello", "hey", "h", "hy", "start"]:
        await start(update, context); return

    if uid not in user_data: return
    state = user_data[uid].get("state")

    if state == "ASK_NAME":
        user_data[uid]["name"] = txt
        user_data[uid]["state"] = "ASK_ADDRESS"
        await update.message.reply_text("📍 Ab apna **Address** likhein:")

    elif state == "ASK_ADDRESS":
        addr = txt
        name = user_data[uid].get("name", "Customer")
        total = user_data[uid].get("total", 0)
        cart = user_data[uid].get("cart", [])
        
        wa_text = f"New Order Confirm:\nName: {name}\nItems: {', '.join(cart)}\nTotal: ₹{total}\nAddress: {addr}"
        wa_link = f"https://wa.me/{MY_PHONE}?text={urllib.parse.quote(wa_text)}"
        
        threading.Thread(target=send_email_now, args=(name, addr, cart, total)).start()
        
        kb = [[InlineKeyboardButton("💬 Send on WhatsApp", url=wa_link)],
              [InlineKeyboardButton("✅ Done & Clear", callback_data='wa_done')]]
        
        await update.message.reply_text(
            f"🎯 *Final Step!* \n\n1. WhatsApp par order bhejein.\n2. Wapas aakar 'Done' dabayein.", 
            reply_markup=InlineKeyboardMarkup(kb), 
            parse_mode='Markdown'
        )

def main():
    threading.Thread(target=run_dummy_server, daemon=True).start()
    app = Application.builder().token(TOKEN).build()
    
    # Handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, handle_web_app_data))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    
    print("Bot with WebApp is Running...")
    app.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    main()
