import os
import smtplib
from email.message import EmailMessage
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

# --- CLOUD SETTINGS (Render Environment Variables) ---
TOKEN = os.getenv("TOKEN")
MY_EMAIL = os.getenv("MY_EMAIL")
APP_PASSWORD = os.getenv("APP_PASSWORD")

user_data = {}

MENU = {
    "burger": {"Cheese Burger": 99, "Chinese Burger": 120, "Veg Maharaja": 150},
    "chinese": {"Veg Manchurian": 120, "Veg Fried Rice": 100, "Hakka Noodles": 110, "Spring Rolls": 80},
    "tea": {"Masala Tea": 20, "Ginger Coffee": 40, "Cold Coffee": 70}
}

def send_order_email(name, address, cart, total):
    items_text = "\n".join([f"• {item} — ₹{price}" for item, price in cart.items()])
    msg = EmailMessage()
    msg.set_content(f"Naya Order!\n\nCustomer: {name}\nAddress: {address}\n\nItems:\n{items_text}\n\nTotal: ₹{total}")
    msg['Subject'] = f"Cafe Order: {name} (₹{total})"
    msg['From'] = MY_EMAIL
    msg['To'] = MY_EMAIL
    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(MY_EMAIL, APP_PASSWORD)
            smtp.send_message(msg)
        return True
    except: return False

async def start(update, context):
    user_id = update.effective_user.id
    user_data[user_id] = {"cart": {}, "total": 0, "state": "ORDERING"}
    keyboard = [[InlineKeyboardButton("🍔 Burgers", callback_data='cat_burger'), InlineKeyboardButton("🍜 Chinese", callback_data='cat_chinese')],
                [InlineKeyboardButton("☕ Drinks", callback_data='cat_tea')],
                [InlineKeyboardButton("🛒 Checkout", callback_data='checkout')]]
    await update.message.reply_text('👋 *Welcome to Ashish Cafe (Cloud)!*', reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')

async def handle_callback(update, context):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    if user_id not in user_data: return
    
    if query.data.startswith('cat_'):
        cat = query.data.split('_')[1]
        kb = [[InlineKeyboardButton(f"{i} (₹{p})", callback_data=f"add_{i}_{p}")] for i, p in MENU[cat].items()]
        kb.append([InlineKeyboardButton("⬅️ Back", callback_data='back_main')])
        await query.edit_message_text(f"--- {cat.upper()} ---", reply_markup=InlineKeyboardMarkup(kb))
    
    elif query.data.startswith('add_'):
        _, item, price = query.data.split('_')
        user_data[user_id]["cart"][item] = user_data[user_id]["cart"].get(item, 0) + int(price)
        user_data[user_id]["total"] += int(price)
        kb = [[InlineKeyboardButton("➕ Add More", callback_data='back_main')], [InlineKeyboardButton("✅ Checkout", callback_data='checkout')]]
        await query.edit_message_text(f"Added {item}! Total: ₹{user_data[user_id]['total']}", reply_markup=InlineKeyboardMarkup(kb))
    
    elif query.data == 'back_main':
        kb = [[InlineKeyboardButton("🍔 Burgers", callback_data='cat_burger'), InlineKeyboardButton("🍜 Chinese", callback_data='cat_chinese')], [InlineKeyboardButton("☕ Drinks", callback_data='cat_tea')], [InlineKeyboardButton("🛒 Checkout", callback_data='checkout')]]
        await query.edit_message_text("Select Category:", reply_markup=InlineKeyboardMarkup(kb))
    
    elif query.data == 'checkout':
        user_data[user_id]["state"] = "ASK_NAME"
        await query.edit_message_text(f"Bill: ₹{user_data[user_id]['total']}\n\nApna *Naam* likhein:", parse_mode='Markdown')

async def handle_text(update, context):
    user_id = update.message.from_user.id
    if user_id not in user_data: return
    state = user_data[user_id].get("state")
    
    if state == "ASK_NAME":
        user_data[user_id]["name"] = update.message.text
        user_data[user_id]["state"] = "ASK_ADDRESS"
        await update.message.reply_text("Ab apna *Delivery Address* likhein:", parse_mode='Markdown')
    
    elif state == "ASK_ADDRESS":
        addr = update.message.text
        name = user_data[user_id]["name"]
        cart = user_data[user_id]["cart"]
        total = user_data[user_id]["total"]
        
        if send_order_email(name, addr, cart, total):
            await update.message.reply_text(f"🎉 Order Confirmed!\n\nShukriya {name}, aapka ₹{total} ka order book ho gaya hai.")
        else:
            await update.message.reply_text("❌ Email bhejte waqt error aaya.")
        del user_data[user_id]

def main():
    if not TOKEN:
        print("Error: TOKEN environment variable not found!")
        return
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    print("Bot is Running on Cloud...")
    app.run_polling()

if __name__ == '__main__':
    main()
