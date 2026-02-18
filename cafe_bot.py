import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
import os

# Bot token (Environment variable se lega)
BOT_TOKEN = os.environ.get("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", 
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Menu data
MENU = {
    "burger": {"name": "🍔 Burger", "price": "₹99 - ₹299"},
    "pizza": {"name": "🍕 Pizza", "price": "₹199 - ₹599"},
    "coffee": {"name": "☕ Coffee", "price": "₹49 - ₹199"},
    "tea": {"name": "🫖 Tea", "price": "₹29 - ₹99"},
    "sandwich": {"name": "🥪 Sandwich", "price": "₹79 - ₹199"},
    "pasta": {"name": "🍝 Pasta", "price": "₹149 - ₹299"},
    "coldrink": {"name": "🥤 Cold Drink", "price": "₹40 - ₹120"},
    "icecream": {"name": "🍦 Ice Cream", "price": "₹59 - ₹199"}
}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a message with menu buttons when /start is issued."""
    keyboard = []
    
    # Create rows of 2 buttons each
    items = list(MENU.keys())
    for i in range(0, len(items), 2):
        row = []
        for j in range(2):
            if i + j < len(items):
                item_key = items[i + j]
                row.append(InlineKeyboardButton(
                    MENU[item_key]["name"], 
                    callback_data=item_key
                ))
        keyboard.append(row)
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "🍽️ **Cafe MEU Mein Aapka Swagat Hai!**\n\n"
        "Kripya apni dish chune:",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle button presses and show price."""
    query = update.callback_query
    await query.answer()
    
    item_key = query.data
    item = MENU.get(item_key)
    
    if item:
        message = f"{item['name']}\n\n💰 **Price: {item['price']}**\n\nKya aap order karna chahenge?"
        
        # Add order button
        keyboard = [[
            InlineKeyboardButton("✅ Order Now", callback_data=f"order_{item_key}"),
            InlineKeyboardButton("🔙 Back to Menu", callback_data="back_to_menu")
        ]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            message,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

async def order_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle order button."""
    query = update.callback_query
    await query.answer()
    
    item_key = query.data.replace("order_", "")
    item = MENU.get(item_key)
    
    if item:
        await query.edit_message_text(
            f"✅ **Order Confirmed!**\n\n"
            f"Aapne {item['name']} order kiya hai.\n"
            f"Total: {item['price']}\n\n"
            f"Dhanyavaad! Aapka order jald hi taiyaar ho jayega. 🙏",
            parse_mode='Markdown'
        )

async def back_to_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Go back to main menu."""
    query = update.callback_query
    await query.answer()
    
    keyboard = []
    items = list(MENU.keys())
    for i in range(0, len(items), 2):
        row = []
        for j in range(2):
            if i + j < len(items):
                item_key = items[i + j]
                row.append(InlineKeyboardButton(
                    MENU[item_key]["name"], 
                    callback_data=item_key
                ))
        keyboard.append(row)
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "🍽️ **Cafe MEU Mein Aapka Swagat Hai!**\n\n"
        "Kripya apni dish chune:",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

def main():
    """Start the bot."""
    # Create the Application
    application = Application.builder().token(BOT_TOKEN).build()

    # Register handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("menu", start))
    
    # Callback query handlers
    application.add_handler(CallbackQueryHandler(button_handler, pattern="^(?!order_|back_to_menu).*$"))
    application.add_handler(CallbackQueryHandler(order_handler, pattern="^order_"))
    application.add_handler(CallbackQueryHandler(back_to_menu, pattern="^back_to_menu$"))

    # Start the bot
    print("Bot started!")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
