import os
import smtplib
import threading
import urllib.parse
from http.server import BaseHTTPRequestHandler, HTTPServer
from email.message import EmailMessage
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

# --- SETTINGS ---
MY_PHONE = "919571646540" 
TOKEN = os.getenv("TOKEN")
MY_EMAIL = os.getenv("MY_EMAIL")
APP_PASSWORD = os.getenv("APP_PASSWORD")

# Health Check for Render
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200); self.end_headers()
        self.wfile.write(b"Bot Active!")
    def do_HEAD(self):
        self.send_response(200); self.end_headers()

def run_dummy_server():
    server = HTTPServer(('0.0.0.0', int(os.environ.get("PORT", 10000))), HealthCheckHandler)
    server.serve_forever()

user_data = {}
MENU = {
    "burger": {"Cheese Burger": 99, "Chinese Burger": 120, "Veg Maharaja": 150},
    "chinese": {"Veg Manchurian": 120, "Veg Fried Rice": 100, "Hakka Noodles": 110, "Spring Rolls": 80},
    "tea": {"Masala Tea": 20, "Ginger Coffee": 40, "Cold Coffee": 70}
}

def send_email_async(name, address, cart, total):
    try:
        items = "\n".join([f"• {item}" for item in cart.keys()])
        msg = EmailMessage()
        msg.set_content(f"Naya Order!\n\nCustomer: {name}\nAddress: {address}\n\nItems:\n{items}\n\nTotal: ₹{total}")
        msg['Subject'] = f"Cafe Order: {name}"; msg['From'] = MY_EMAIL; msg['To'] = MY_EMAIL
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(MY_EMAIL, APP_PASSWORD)
            smtp.send_message(msg)
    except: pass

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_data[user_id] = {"cart": {}, "total": 0, "state": "ORDERING"}
    kb = [[InlineKeyboardButton("🍔 Burgers", callback_data='cat_burger'), InlineKeyboardButton("🍜 Chinese", callback_data='cat_chinese')],
          [InlineKeyboardButton("☕ Drinks", callback_data='cat_tea')],
          [InlineKeyboardButton("🛒 Checkout", callback_data='checkout')]]
    await update.message.reply_text('👋 *Welcome to Crushescafe!*\n\nKya khana pasand karenge?', reply_markup=InlineKeyboardMarkup(kb), parse_mode='Markdown')

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query; await query.answer()
    user_id = query.from_user.id
    if user_id not in user_data: return
    
    # --- WhatsApp Button Click Handle (Button hatane ke liye) ---
    if query.data == 'wa_done':
        await query.edit_message_text("✅ *Order Successfully Placed!*\n\nAapka order kitchen mein bhej diya gaya hai. Hum jaldi hi aapke paas honge. Thank you! 🙏", parse_mode='Markdown')
        if user_id in user_data: del user_data[user_id]
        return

    if query.data.startswith('cat_'):
        cat = query.data.split('_')[1]
        kb = [[InlineKeyboardButton(f"{i} (₹{p})", callback_data=f"add_{i}_{p}")] for i, p in MENU[cat].items()]
        kb.append([InlineKeyboardButton("⬅️ Back", callback_data='back_main')])
        await query.edit_message_text(f"--- {cat.upper()} MENU ---", reply_markup=InlineKeyboardMarkup(kb))
    
    elif query.data.startswith('add_'):
        _, item, price = query.data.split('_')
        user_data[user_id]["cart"][item] = user_data[user_id]["cart"].get(item, 0) + int(price)
        user_data[user_id]["total"] += int(price)
        kb = [[InlineKeyboardButton("➕ Add More", callback_data='back_main')], [InlineKeyboardButton("✅ Checkout", callback_data='checkout')]]
        await query.edit_message_text(f"Added {item}! Total: ₹{user_data[user_id]['total']}", reply_markup=InlineKeyboardMarkup(kb))

    elif query.data == 'back_main':
        kb = [[InlineKeyboardButton("🍔 Burgers", callback_data='cat_burger'), InlineKeyboardButton("🍜 Chinese", callback_data='cat_chinese')], [InlineKeyboardButton("☕ Drinks", callback_data='cat_tea')], [InlineKeyboardButton("🛒 Checkout", callback_data='checkout')]]
        await query.edit_message_text("Category chunein:", reply_markup=InlineKeyboardMarkup(kb))

    elif query.data == 'checkout':
        if not user_data[user_id]["cart"]:
            await query.edit_message_text("Cart khali hai!"); return
        user_data[user_id]["state"] = "ASK_NAME"
        await query.edit_message_text(f"Total Bill: ₹{user_data[user_id]['total']}\n\nApna *Naam* likhein:", parse_mode='Markdown')

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    text = update.message.text.lower()

    # --- Hi/Hello se shuru karne ka jugadh ---
    if text in ["hi", "hello", "start", "hey"]:
        await start(update, context); return

    if user_id not in user_data: return
    state = user_data[user_id].get("state")

    if state == "ASK_NAME":
        user_data[user_id]["name"] = update.message.text
        user_data[user_id]["state"] = "ASK_ADDRESS"
        await update.message.reply_text("Ab apna *Delivery Address* likhein:")

    elif state == "ASK_ADDRESS":
        addr = update.message.text
        name = user_data[user_id].get("name", "Customer")
        total = user_data[user_id].get("total", 0)
        cart = user_data[user_id].get("cart", {})
        
        wa_text = f"New Order Confirm:\nName: {name}\nItems: {', '.join(cart.keys())}\nTotal: ₹{total}\nAddress: {addr}"
        wa_link = f"https://wa.me/{MY_PHONE}?text={urllib.parse.quote(wa_text)}"
        
        # Email background thread mein chalega taaki reply instant ho
        threading.Thread(target=send_email_async, args=(name, addr, cart, total)).start()
        
        # WhatsApp button + Ek 'Done' button button gayab karne ke liye
        kb = [[InlineKeyboardButton("💬 Open WhatsApp & Send", url=wa_link)],
              [InlineKeyboardButton("✅ Click here AFTER Sending", callback_data='wa_done')]]
        
        await update.message.reply_text(f"🎉 *Order Ready!*\n\n1. Pehle WhatsApp button dabakar message send karein.\n2. Phir niche wala 'Confirm' button dabayein.", 
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
