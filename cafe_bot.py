import smtplib
from email.message import EmailMessage
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# --- Configuration ---
TOKEN = 'YOUR_BOT_TOKEN'
MY_EMAIL = "apka-email@gmail.com"  # Jaha mail aana chahiye
APP_PASSWORD = "your-app-password" # Gmail ka App Password (Normal password nahi)

# Email bhejne ka function
def send_order_email(user_name, order_details):
    msg = EmailMessage()
    msg.set_content(f"Naya Order Aaya Hai!\n\nCustomer Name: {user_name}\nOrder: {order_details}")
    msg['Subject'] = f"New Cafe Order from {user_name}"
    msg['From'] = MY_EMAIL
    msg['To'] = MY_EMAIL

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(MY_EMAIL, APP_PASSWORD)
            smtp.send_message(msg)
    except Exception as e:
        print(f"Error sending email: {e}")

# Jab user apna naam likhega tab order confirm hoga
async def handle_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_name = update.message.text
    order_item = "1x Veg Burger" # Yeh aap dynamic bhi bana sakte hain
    
    # Mail bhejein
    send_order_email(user_name, order_item)
    
    await update.message.reply_text(f"Dhanyawad {user_name}! Aapka order book ho gaya hai aur humein mail mil gaya hai.")

def main():
    app = Application.builder().token(TOKEN).build()
    
    # User jab text message (naam) bhejega tab ye chalega
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_order))
    
    print("Bot is running...")
    app.run_polling()

if __name__ == '__main__':
    main()
