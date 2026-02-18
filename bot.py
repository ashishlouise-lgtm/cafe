import smtplib
from email.message import EmailMessage
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

# --- CONFIGURATION ---
TOKEN = 'YOUR_TELEGRAM_BOT_TOKEN'
MY_EMAIL = "apka-email@gmail.com"      # Jahan order receive karna hai
APP_PASSWORD = "your-app-password"      # 16-digit Google App Password

# Dictionary to store user's current selection temporarily
user_orders = {}

# --- EMAIL FUNCTION ---
def send_order_email(user_name, item_name):
    msg = EmailMessage()
    msg.set_content(f"Naya Order Aaya Hai!\n\nCustomer Name: {user_name}\nItem: {item_name}")
    msg['Subject'] = f"Cafe Order: {item_name} by {user_name}"
    msg['From'] = MY_EMAIL
    msg['To'] = MY_EMAIL

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(MY_EMAIL, APP_PASSWORD)
            smtp.send_message(msg)
        return True
    except Exception as e:
        print(f"Email Error: {e}")
        return False

# --- HANDLERS ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🍔 Burger Menu", callback_data='burger_cat')],
        [InlineKeyboardButton("☕ Tea Menu", callback_data='tea_cat')],
        [InlineKeyboardButton("📍 Address", callback_data='address'),
         InlineKeyboardButton("📞 Phone", callback_data='phone')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text('☕ *Welcome to Our Cafe!* \nNiche diye gaye options se order karein:', 
                                  reply_markup=reply_markup, parse_mode='Markdown')

async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == 'burger_cat':
        keyboard = [
            [InlineKeyboardButton("Veg Burger - ₹99", callback_data='order_Veg Burger')],
            [InlineKeyboardButton("Cheese Burger - ₹129", callback_data='order_Cheese Burger')],
            [InlineKeyboardButton("⬅️ Back", callback_data='main_menu')]
        ]
        await query.edit_message_text("🍔 *Burgers Selection:*", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')

    elif query.data == 'tea_cat':
        keyboard = [
            [InlineKeyboardButton("Masala Tea - ₹20", callback_data='order_Masala Tea')],
            [InlineKeyboardButton("Ginger Tea - ₹25", callback_data='order_Ginger Tea')],
            [InlineKeyboardButton("⬅️ Back", callback_data='main_menu')]
        ]
        await query.edit_message_text("☕ *Tea Selection:*", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')

    elif query.data.startswith('order_'):
        item = query.data.replace('order_', '')
        user_orders[query.from_user.id] = item # Store item
        await query.edit_message_text(f"✅ Aapne *{item}* select kiya hai.\n\nAb apna **Pura Naam** type karke bhejein taaki hum order confirm kar sakein.", parse_mode='Markdown')

    elif query.data == 'address':
        await query.edit_message_text("📍 *Address:* Shop No. 5, Food Street, New Delhi.\n\n[Back to Menu](t.me/yourbotusername)", parse_mode='Markdown')

    elif query.data == 'phone':
        await query.edit_message_text("📞 *Contact:* +91 9876543210\nTiming: 10 AM - 11 PM", parse_mode='Markdown')

    elif query.data == 'main_menu':
        await start(query, context)

async def handle_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if user_id in user_orders:
        user_name = update.message.text
        item_ordered = user_orders[user_id]
        
        # Send Email
        success = send_order_email(user_name, item_ordered)
        
        if success:
            await update.message.reply_text(f"🎉 Shukriya {user_name}!\n\nAapka *{item_ordered}* ka order book ho gaya hai. Humne cafe manager ko mail bhej diya hai.")
        else:
            await update.message.reply_text("❌ Sorry, mail bhejne mein error aaya. Manager ko call karein.")
        
        del user_orders[user_id] # Clear order session
    else:
        await update.message.reply_text("Pehle menu se koi item select karein! Type /start")

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_click))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_name))
    
    print("Cafe Bot is LIVE...")
    app.run_polling()

if __name__ == '__main__':
    main()
