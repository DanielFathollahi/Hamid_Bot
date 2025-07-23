import os
from flask import Flask, request
from telegram import (
    Bot, Update, InlineKeyboardButton, InlineKeyboardMarkup
)
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler, MessageHandler,
    ConversationHandler, ContextTypes, filters
)
import logging

# اطلاعات حساس
BOT_TOKEN = os.environ["BOT_TOKEN"]
GROUP_CHAT_ID = os.environ["GROUP_CHAT_ID"]  # مثلاً: -1001234567890

# مراحل گفتگو
LANGUAGE, MENU, FULLNAME, PHONE, EMAIL, JOB = range(6)

# فعال‌سازی لاگ‌ها
logging.basicConfig(level=logging.INFO)

app = Flask(__name__)
bot = Bot(BOT_TOKEN)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🇮🇷 فارسی", callback_data="fa")],
        [InlineKeyboardButton("🇺🇸 English", callback_data="en")],
        [InlineKeyboardButton("🇸🇦 عربی", callback_data="ar")],
        [InlineKeyboardButton("🇨🇳 چینی", callback_data="zh")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("🌍 لطفاً زبان خود را انتخاب کنید:", reply_markup=reply_markup)
    return LANGUAGE

async def select_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = update.callback_query.data
    context.user_data["lang"] = lang
    await update.callback_query.answer()

    text = {
        'fa': "📌 معرفی: حمید فتح‌اللهی\n\nسلام و خوش‌آمدید 🌟\nمن حمید فتح‌اللهی هستم...",
        'en': "📌 About: Hamid Fathollahi\n\nWelcome 🌟\nI’m Hamid Fathollahi...",
        'ar': "📌 تعريف: حميد فتح اللهي\n\nأهلاً وسهلاً 🌟\nأنا حميد فتح اللهي...",
        'zh': "📌 简介：Hamid Fathollahi\n\n欢迎 🌟\n我是 Hamid Fathollahi..."
    }

    await update.callback_query.message.reply_text(text[lang])

    keyboard = [[InlineKeyboardButton("🤝 همکاری با ما", callback_data="cooperate")]]
    await update.callback_query.message.reply_text("برای همکاری، دکمه زیر را بزنید:", reply_markup=InlineKeyboardMarkup(keyboard))
    return MENU

async def cooperate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    await update.callback_query.message.reply_text("نام و نام خانوادگی خود را وارد کنید:")
    return FULLNAME

async def get_fullname(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["fullname"] = update.message.text
    await update.message.reply_text("شماره تماس خود را وارد کنید:")
    return PHONE

async def get_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["phone"] = update.message.text
    await update.message.reply_text("ایمیل خود را وارد کنید:")
    return EMAIL

async def get_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["email"] = update.message.text
    await update.message.reply_text("اطلاعات شغلی خود را وارد کنید:")
    return JOB

async def get_job(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["job"] = update.message.text

    user = update.message.from_user
    fullname = context.user_data["fullname"]
    phone = context.user_data["phone"]
    email = context.user_data["email"]
    job = context.user_data["job"]

    msg = (
        "📥 فرم همکاری جدید:\n"
        f"👤 نام: {fullname}\n"
        f"📞 تلفن: {phone}\n"
        f"📧 ایمیل: {email}\n"
        f"💼 شغل: {job}\n"
        f"🆔 آیدی عددی: {user.id}\n"
        f"👤 یوزرنیم: @{user.username if user.username else 'ندارد'}"
    )

    await bot.send_message(chat_id=GROUP_CHAT_ID, text=msg)
    await update.message.reply_text("✅ اطلاعات شما ارسال شد. با تشکر 🙏")
    return ConversationHandler.END

def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    return ConversationHandler.END

# راه‌اندازی بات
application = Application.builder().token(BOT_TOKEN).build()

conv_handler = ConversationHandler(
    entry_points=[CommandHandler("start", start)],
    states={
        LANGUAGE: [CallbackQueryHandler(select_language)],
        MENU: [CallbackQueryHandler(cooperate)],
        FULLNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_fullname)],
        PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_phone)],
        EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_email)],
        JOB: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_job)],
    },
    fallbacks=[CommandHandler("cancel", cancel)],
    allow_reentry=True
)

application.add_handler(conv_handler)

# اجرای فلاسک برای اتصال به UptimeRobot
@app.route('/')
def home():
    return "بات آنلاین است."

@app.route('/webhook', methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), bot)
    application.update_queue.put_nowait(update)
    return "ok"

if __name__ == '__main__':
    application.run_polling()
