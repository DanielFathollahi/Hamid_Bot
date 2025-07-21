import os
import threading
from flask import Flask
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    ConversationHandler, ContextTypes, filters
)

TOKEN = os.getenv("TOKEN")
GROUP_CHAT_ID = -1002542201765

app = Flask(__name__)

@app.route('/')
def ping():
    return 'pong'

ASK_DESCRIPTION, ASK_PHONE = range(2)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    intro_text = """
📌 معرفی: حمید فتح‌اللهی

سلام و خوش‌آمدید 🌟

من حمید فتح‌اللهی هستم، فعال در حوزه تولید و عرضه انواع پیگمنت‌های معدنی قابل استفاده در:
🎨 سفال، سرامیک، فلز، شیشه و سیمان

همچنین:
🌏 واردکننده محصولات از کشورهای شرقی
🚢 صادرکننده به بازارهای عربی و غربی

✨ محصولات ما شامل طیف گسترده‌ای از:
🏗️ مصالح ساختمانی
🌱 محصولات کشاورزی
💎 و مواد اولیه صنعت طلا
"""
    await update.message.reply_text(intro_text)
    await update.message.reply_text("لطفاً درباره کار خود و خودتان توضیح دهید ✍️")
    return ASK_DESCRIPTION

async def ask_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["description"] = update.message.text
    keyboard = [[KeyboardButton("📱 ارسال شماره", request_contact=True)]]
    markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    await update.message.reply_text("لطفاً شماره تلفن خود را ارسال کنید 📱", reply_markup=markup)
    return ASK_PHONE

async def collect(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    contact = update.message.contact
    phone = contact.phone_number if contact else update.message.text
    description = context.user_data.get("description", "")

    msg = (
        f"👤 {user.first_name} {user.last_name or ''}\n"
        f"🆔 {user.id}\n"
        f"🔗 @{user.username or 'ندارد'}\n"
        f"📝 {description}\n"
        f"📞 {phone}"
    )

    await context.bot.send_message(GROUP_CHAT_ID, msg)
    await update.message.reply_text("✅ اطلاعات شما ثبت شد. ممنون 🙏")
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("لغو شد.")
    return ConversationHandler.END

def run_bot():
    app_tg = Application.builder().token(TOKEN).build()
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            ASK_DESCRIPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_phone)],
            ASK_PHONE: [
                MessageHandler(filters.CONTACT, collect),
                MessageHandler(filters.TEXT & ~filters.COMMAND, collect)
            ]
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )
    app_tg.add_handler(conv_handler)
    app_tg.run_polling()

if __name__ == "__main__":
    threading.Thread(target=lambda: app.run(host="0.0.0.0", port=8000)).start()
    run_bot()
