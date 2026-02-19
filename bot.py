import os
import json
import smtplib
import threading
import urllib.parse
from http.server import BaseHTTPRequestHandler, HTTPServer
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, WebAppInfo
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

# --- CONFIG ---
MY_PHONE = "919571646540" 
TOKEN = os.getenv("TOKEN")
MY_EMAIL = os.getenv("MY_EMAIL")
APP_PASSWORD = os.getenv("APP_PASSWORD")
WEB_LINK = "https://ashishlouise-lgtm.github.io/cafe/" # Link sahi hai

user_data = {}

async def start(update, context):
    uid = update.effective_user.id
    user_data[uid] = {"cart": [], "total": 0, "state": "ORDERING"}
    kb = [[InlineKeyboardButton("📱 Open Menu Website", web_app=WebAppInfo(url=WEB_LINK))]]
    await update.message.reply_text("✨ *Welcome!* ✨\nNiche button se order karein:", reply_markup=InlineKeyboardMarkup(kb), parse_mode='Markdown')

async def handle_web_app_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Is function se 'Confirm Order' ka data bot ke paas aayega"""
    uid = update.effective_user.id
    raw_data = update.effective_message.web_app_data.data
    data = json.loads(raw_data)
    
    user_data[uid] = {
        "cart": data['items'],
        "total": data['total'],
        "state": "ASK_NAME"
    }
    
    await update.message.reply_text(f"🧾 *Order Summary:*\nTotal: ₹{data['total']}\n\nAb apna **Naam** likhein:", parse_mode='Markdown')

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
        await update.message.reply_text("📍 Ab apna **Address** batayein:")

    elif state == "ASK_ADDRESS":
        # Yahan WhatsApp link aur Email wala logic aayega (Same as before)
        name = user_data[uid]["name"]
        total = user_data[uid]["total"]
        items = ", ".join(user_data[uid]["cart"])
        wa_text = f"New Order: {name}\nItems: {items}\nTotal: ₹{total}\nAddress: {txt}"
        wa_link = f"https://wa.me/{MY_PHONE}?text={urllib.parse.quote(wa_text)}"
        
        kb = [[InlineKeyboardButton("💬 Confirm on WhatsApp", url=wa_link)]]
        await update.message.reply_text("🎉 *Order Ready!* WhatsApp par confirm karein:", reply_markup=InlineKeyboardMarkup(kb), parse_mode='Markdown')
        del user_data[uid]

def main():
    # Render Health Check (Dummy Server)
    threading.Thread(target=lambda: HTTPServer(('0.0.0.0', int(os.environ.get("PORT", 10000))), BaseHTTPRequestHandler).serve_forever(), daemon=True).start()
    
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    # YE LINE SABSE ZAROORI HAI:
    app.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, handle_web_app_data))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    
    print("Bot is Starting...")
    app.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    main()
