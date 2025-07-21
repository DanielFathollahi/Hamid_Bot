import os
import threading

from flask import Flask
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    filters, ContextTypes, ConversationHandler
)

TOKEN = os.environ["TOKEN"]
GROUP_CHAT_ID = -1002542201765

app = Flask(__name__)

@app.route('/ping')
def ping():
    return 'pong'

# مراحل گفتگو
ASK_DESCRIPTION, ASK_PHONE = range(2)

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

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(intro_text)
    await update.message.reply_text("لطفاً درباره کار خود و خودتان توضیح بدهید ✍️")
    return ASK_DESCRIPTION

async def ask_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["description"] = update.message.text

    keyboard = [[KeyboardButton("📱 ارسال شماره", request_contact=True)]]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    await update.message.reply_text(
        "جهت کسب اطلاعات بیشتر یا همکاری، لطفاً شماره تلفن خود را ارسال کنید. 📱",
        reply_markup=reply_markup
    )
    return ASK_PHONE

async def collect_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    contact = update.message.contact
    phone_number = contact.phone_number if contact else update.message.text

    description = context.user_data.get("description", "ندارد")

    msg = (
        f"📥 اطلاعات جدید از کاربر:\n\n"
        f"👤 نام: {user.first_name} {user.last_name or ''}\n"
        f"🆔 آیدی عددی: {user.id}\n"
        f"🔗 یوزرنیم: @{user.username if user.username else 'ندارد'}\n"
        f"📝 توضیحات: {description}\n"
        f"📞 شماره: {phone_number}"
    )

    await context.bot.send_message(chat_id=GROUP_CHAT_ID, text=msg)

    await update.message.reply_text("✅ اطلاعات شما ثبت شد. ممنون از شما 🙏")

    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("گفتگو لغو شد.")
    return ConversationHandler.END

def run_bot():
    app_telegram = ApplicationBuilder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            ASK_DESCRIPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_phone)],
            ASK_PHONE: [
                MessageHandler(filters.CONTACT, collect_data),
                MessageHandler(filters.TEXT & ~filters.COMMAND, collect_data),
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app_telegram.add_handler(conv_handler)

    print("ربات در حال اجراست...")
    app_telegram.run_polling()

if __name__ == "__main__":
    threading.Thread(target=lambda: app.run(host="0.0.0.0", port=8000)).start()
    run_bot()
