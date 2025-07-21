import os
import threading
import asyncio
import re
from flask import Flask
from telegram import (
    Update, KeyboardButton, ReplyKeyboardMarkup
)
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    ContextTypes, filters, ConversationHandler
)

TOKEN = os.environ["TOKEN"]
GROUP_CHAT_ID = -1002542201765

app = Flask(__name__)

ASK_DESCRIPTION, ASK_PHONE = range(2)

@app.route('/ping')
def ping():
    return 'pong'


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    intro = """
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
    await update.message.reply_text(intro)
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

    # اعتبارسنجی شماره تلفن ساده
    if not re.match(r"^\+?\d{10,15}$", phone):
        await update.message.reply_text("شماره تلفن وارد شده معتبر نیست، لطفاً دوباره تلاش کنید.")
        return ASK_PHONE

    msg = (
        f"👤 نام: {user.first_name} {user.last_name or ''}\n"
        f"🆔 آیدی عددی: {user.id}\n"
        f"🔗 یوزرنیم: @{user.username or 'ندارد'}\n"
        f"📝 توضیحات: {description}\n"
        f"📞 شماره: {phone}"
    )

    await context.bot.send_message(chat_id=GROUP_CHAT_ID, text=msg)
    await update.message.reply_text("✅ اطلاعات شما ثبت شد. ممنون 🙏", reply_markup=ReplyKeyboardMarkup([["شروع مجدد"]], resize_keyboard=True))
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("لغو شد.")
    return ConversationHandler.END


async def run_bot():
    app_telegram = ApplicationBuilder().token(TOKEN).build()

    # حذف webhook اگر ست شده
    await app_telegram.bot.delete_webhook()

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

    app_telegram.add_handler(conv_handler)

    print("ربات در حال اجراست...")
    await app_telegram.run_polling()


if __name__ == "__main__":
    # اجرای وب‌سرور Flask در Thread جدا
    threading.Thread(target=lambda: app.run(host="0.0.0.0", port=8000)).start()

    # اجرای ربات تلگرام در event loop موجود
    loop = asyncio.get_event_loop()
    loop.create_task(run_bot())
    loop.run_forever()
