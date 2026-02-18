    import os
import smtplib
import threading
import urllib.parse
from datetime import datetime
from http.server import BaseHTTPRequestHandler, HTTPServer
from email.message import EmailMessage
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

# --- SETTINGS ---
MY_PHONE = "919571646540" 
TOKEN = os.getenv("TOKEN")
MY_EMAIL = os.getenv("MY_EMAIL")
APP_PASSWORD = os.getenv("APP_PASSWORD")

class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200); self.end_headers()
        self.wfile.write(b"Bot Stylish and Online!")
    def do_HEAD(self):
        self.send_response(200); self.end_headers()

def run_dummy_server():
    server = HTTPServer(('0.0.0.0', int(os.environ.get("PORT", 10000))), HealthCheckHandler)
    server.serve_forever()

user_data = {}
MENU = {
    "burger": {"🍔 Cheese Burger": 99, "🍔 Chinese Burger": 120, "🍔 Veg Maharaja": 150},
    "chinese": {"🍜 Veg Manchurian": 120, "🍜 Veg Fried Rice": 100, "🍜 Hakka Noodles": 110, "🌯 Spring Rolls": 80},
    "tea": {"☕ Masala Tea": 20, "☕ Ginger Coffee": 40, "🥤 Cold Coffee": 70}
}

def send_email_now(name, address, cart, total):
    try:
        now = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
        items = "\n".join([f"• {item}" for item in cart.keys()])
        msg = EmailMessage()
        msg.set_content(f"Naya Order!\n\nWaqt: {now}\nCustomer: {name}\nAddress: {address}\n\nItems:\n{items}\n\nTotal: ₹{total}")
        msg['Subject'] = f"Cafe Order: {name} (₹{total})"; msg['From'] = MY_EMAIL; msg['To'] = MY_EMAIL
        with smtplib.SMTP_SSL('smtp.gmail.com', 465, timeout=10) as smtp:
            smtp.login(MY_EMAIL, APP_PASSWORD)
            smtp.send_message(msg)
    except: pass

async def start(update, context):
    user_id = update.effective_user.id
    user_data[user_id] = {"cart": {}, "total": 0, "state": "ORDERING"}
    kb = [[InlineKeyboardButton("🍔 Burgers", callback_data='cat_burger'), InlineKeyboardButton("🍜 Chinese Special", callback_data='cat_chinese')],
          [InlineKeyboardButton("☕ Drinks & Tea", callback_data='cat_tea')],
          [InlineKeyboardButton("🛒 View Bill", callback_data='checkout'), InlineKeyboardButton("❌ Cancel", callback_data='cancel')]]
    await update.message.reply_text('✨ *Welcome to Crushescafe!* ✨\n\nHum aapke liye kya laayein?', reply_markup=InlineKeyboardMarkup(kb), parse_mode='Markdown')

async def handle_callback(update, context):
    query = update.callback_query; await query.answer()
    user_id = query.from_user.id
    if user_id not in user_data: return
    
    if query.data == 'cancel':
        await query.edit_message_text("❌ *Order Cancelled!* \nJab bhi kuch khane ka mann ho, 'Hi' likhein.", parse_mode='Markdown')
        del user_data[user_id]; return

    if query.data == 'wa_done':
        await query.edit_message_text("💖 *Thank You!* \nAapka order jald hi taiyaar ho jayega. Please wait karein! 🙏", parse_mode='Markdown')
        return

    if query.data.startswith('cat_'):
        cat = query.data.split('_')[1]
        kb = [[InlineKeyboardButton(f"{i} (₹{p})", callback_data=f"add_{i}_{p}")] for i, p in MENU[cat].items()]
        kb.append([InlineKeyboardButton("⬅️ Back to Menu", callback_data='back_main')])
        await query.edit_message_text(f"🔥 *{cat.upper()} SELECTION* 🔥", reply_markup=InlineKeyboardMarkup(kb), parse_mode='Markdown')
    
    elif query.data.startswith('add_'):
        _, item, price = query.data.split('_')
        user_data[user_id]["cart"][item] = user_data[user_id]["cart"].get(item, 0) + int(price)
        user_data[user_id]["total"] += int(price)
        kb = [[InlineKeyboardButton("➕ Add More", callback_data='back_main')], [InlineKeyboardButton("💳 Final Bill", callback_data='checkout')]]
        await query.edit_message_text(f"✅ *{item}* add ho gaya!\n\n💰 Total: *₹{user_data[user_id]['total']}*", reply_markup=InlineKeyboardMarkup(kb), parse_mode='Markdown')

    elif query.data == 'back_main':
        kb = [[InlineKeyboardButton("🍔 Burgers", callback_data='cat_burger'), InlineKeyboardButton("🍜 Chinese", callback_data='cat_chinese')],
              [InlineKeyboardButton("☕ Drinks", callback_data='cat_tea')],
              [InlineKeyboardButton("🛒 View Bill", callback_data='checkout'), InlineKeyboardButton("❌ Cancel", callback_data='cancel')]]
        await query.edit_message_text("Category chunein:", reply_markup=InlineKeyboardMarkup(kb))

    elif query.data == 'checkout':
        user_data[user_id]["state"] = "ASK_NAME"
        await query.edit_message_text(f"🧾 *ORDER BILL:* ₹{user_data[user_id]['total']}\n\nAb apna pyara sa **Naam** batayein:", parse_mode='Markdown')

async def handle_text(update, context):
    user_id = update.message.from_user.id
    text = update.message.text.lower()

    if text in ["hi", "hello", "hey", "start", "menu"]:
        await start(update, context); return

    if user_id not in user_data: return
    state = user_data[user_id].get("state")

    if state == "ASK_NAME":
        user_data[user_id]["name"] = update.message.text
        user_data[user_id]["state"] = "ASK_ADDRESS"
        await update.message.reply_text("📍 *Great!* Ab apna **Delivery Address** likhein:")

    elif state == "ASK_ADDRESS":
        addr = update.message.text
        name = user_data[user_id].get("name", "Customer")
        total = user_data[user_id].get("total", 0)
        cart = user_data[user_id].get("cart", {})
        
        wa_text = f"New Order Confirm:\nName: {name}\nItems: {', '.join(cart.keys())}\nTotal: ₹{total}\nAddress: {addr}"
        wa_link = f"https://wa.me/{MY_PHONE}?text={urllib.parse.quote(wa_text)}"
        
        threading.Thread(target=send_email_now, args=(name, addr, cart, total)).start()
        
        kb = [[InlineKeyboardButton("💬 WhatsApp par Bhejein", url=wa_link)],
              [InlineKeyboardButton("✅ Confirm & Done", callback_data='wa_done')]]
        
        await update.message.reply_text(f"🎯 *Final Step!* \n\n1. WhatsApp button dabakar order send karein.\n2. Wapas aakar 'Confirm' dabayein.", 
                                      reply_markup=InlineKeyboardMarkup(kb), parse_mode='Markdown')

def main():
    threading.Thread(target=run_dummy_server, daemon=True).start()
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    main()
