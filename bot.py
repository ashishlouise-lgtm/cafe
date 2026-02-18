import os
import smtplib
import threading
import urllib.parse
from http.server import BaseHTTPRequestHandler, HTTPServer
from email.message import EmailMessage
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

# --- SETTINGS ---
MY_PHONE = "918078619566" 
TOKEN = os.getenv("TOKEN")
MY_EMAIL = os.getenv("MY_EMAIL")
APP_PASSWORD = os.getenv("APP_PASSWORD")

# Health Check for Render
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is Zinda!")
    def do_HEAD(self):
        self.send_response(200)
        self.end_headers()

def run_dummy_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(('0.0.0.0', port), HealthCheckHandler)
    server.serve_forever()

user_data = {}
MENU = {
    "burger": {"Cheese Burger": 99, "Chinese Burger": 120, "Veg Maharaja": 150},
    "chinese": {"Veg Manchurian": 120, "Veg Fried Rice": 100, "Hakka Noodles": 110, "Spring Rolls": 80},
    "tea": {"Masala Tea": 20, "Ginger Coffee": 40, "Cold Coffee": 70}
}

def send_order_email(name, address, cart, total):
    try:
        items_text = "\n".join([f"• {item}" for item in cart.keys()])
        msg = EmailMessage()
        msg.set_content(f"Naya Order!\n\nCustomer: {name}\nAddress: {address}\n\nItems:\n{items_text}\n\nTotal: ₹{total}")
        msg['Subject'] = f"Cafe Order: {name} (₹{total})"
        msg['From'] = MY_EMAIL
        msg['To'] = MY_EMAIL
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(MY_EMAIL, APP_PASSWORD)
            smtp.send_message(msg)
        return True
    except Exception as e:
        print(f"Email Error: {e}")
        return False

async def start(update, context):
    user_id = update.effective_user.id
    user_data[user_id] = {"cart": {}, "total": 0, "state": "ORDERING"}
    kb = [[InlineKeyboardButton("🍔 Burgers", callback_data='cat_burger'), InlineKeyboardButton("🍜 Chinese", callback_data='cat_chinese')],
          [InlineKeyboardButton("☕ Drinks", callback_data='cat_tea')],
          [InlineKeyboardButton("🛒 Checkout", callback_data='checkout')]]
    await update.message.reply_text('👋 *Welcome to Crushescafe!*', reply_markup=InlineKeyboardMarkup(kb), parse_mode='Markdown')

async def handle_callback(update, context):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    if user_id not in user_data: return
    
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
            await query.edit_message_text("Cart khali hai! /start")
            return
        user_data[user_id]["state"] = "ASK_NAME"
        await query.edit_message_text(f"Total Bill: ₹{user_data[user_id]['total']}\n\nApna *Naam* likhein:", parse_mode='Markdown')

async def handle_text(update, context):
    user_id = update.message.from_user.id
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
        
        # WhatsApp Link Generation
        items_list = ", ".join(cart.keys())
        wa_text = f"New Order: \nName: {name}\nItems: {items_list}\nTotal: ₹{total}\nAddress: {addr}"
        wa_link = f"https://wa.me/{MY_PHONE}?text={urllib.parse.quote(wa_text)}"
        
        # Email bhejte waqt error aaye toh bhi WhatsApp button dikhao
        send_order_email(name, addr, cart, total)
        
        kb = [[InlineKeyboardButton("💬 Confirm on WhatsApp", url=wa_link)]]
        await update.message.reply_text(f"🎉 *Order Processed!*\n\nNiche button par click karke WhatsApp par order confirm karein:", 
                                      reply_markup=InlineKeyboardMarkup(kb), parse_mode='Markdown')
        
        # Session reset
        del user_data[user_id]

def main():
    threading.Thread(target=run_dummy_server, daemon=True).start()
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    print("Bot is Starting...")
    app.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    main()
