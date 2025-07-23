import os
import threading
from datetime import datetime
from telegram import (
    Update, KeyboardButton, ReplyKeyboardMarkup,
    InlineKeyboardButton, InlineKeyboardMarkup
)
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler, MessageHandler,
    ConversationHandler, ContextTypes, filters
)
import requests
from flask import Flask

TOKEN = os.getenv("TOKEN")
HF_TOKEN = os.getenv("HF_TOKEN")
GROUP_CHAT_ID = -1002542201765
HF_MODEL = "mistralai/Mistral-7B-Instruct-v0.2"
HF_API_URL = f"https://api-inference.huggingface.co/models/{HF_MODEL}"
HEADERS = {"Authorization": f"Bearer {HF_TOKEN}"}

ASK_LANGUAGE, CHOOSE_OPTION, ASK_NAME, ASK_JOB, ASK_PHONE, ASK_EMAIL, AI_CHAT = range(7)
user_daily_usage = {}

translations = {
    'fa': {
        'intro': """...""",
        'ask_name': "لطفاً نام و نام خانوادگی خود را وارد کنید ✍️",
        'ask_job': "لطفاً اطلاعات شغلی خود را بنویسید ✍️",
        'ask_phone': "لطفاً شماره تلفن خود را ارسال کنید 📱",
        'ask_email': "لطفاً ایمیل خود را وارد کنید 📧",
        'thanks': "✅ اطلاعات شما ثبت شد. ممنون 🙏",
        'cancel': "لغو شد.",
        'choose_option': "لطفاً یکی از گزینه‌های زیر را انتخاب کنید:",
        'ai_limit_reached': "❌ شما امروز به حد مجاز ۵ پیام چت با هوش مصنوعی رسیدید.",
        'ai_wait': "در حال پردازش پاسخ..."
    },
    'en': {
        'intro': "📌 About Me & Cooperation: ...",
        'ask_name': "Please enter your full name ✍️",
        'ask_job': "Please describe your job ✍️",
        'ask_phone': "Please send your phone number 📱",
        'ask_email': "Please enter your email 📧",
        'thanks': "✅ Your info has been saved. Thank you 🙏",
        'cancel': "Cancelled.",
        'choose_option': "Please choose one of the options below:",
        'ai_limit_reached': "❌ You've hit today's 5-message AI limit.",
        'ai_wait': "Processing AI response..."
    }
}

def can_send_message(user_id):
    today = datetime.now().date()
    if user_id in user_daily_usage:
        last_date, count = user_daily_usage[user_id]
        if last_date == today:
            return count < 5
        user_daily_usage[user_id] = (today, 0)
        return True
    user_daily_usage[user_id] = (today, 0)
    return True

def increase_message_count(user_id):
    today = datetime.now().date()
    last_date, count = user_daily_usage.get(user_id, (today, 0))
    if last_date == today:
        user_daily_usage[user_id] = (today, count + 1)
    else:
        user_daily_usage[user_id] = (today, 1)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    markup = InlineKeyboardMarkup([
        [InlineKeyboardButton("🇮🇷 فارسی", callback_data='fa'), InlineKeyboardButton("🇬🇧 English", callback_data='en')]
    ])
    await update.message.reply_text("لطفاً زبان خود را انتخاب کنید 🌐", reply_markup=markup)
    return ASK_LANGUAGE

async def choose_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    lang = query.data
    context.user_data['lang'] = lang
    markup = InlineKeyboardMarkup([
        [InlineKeyboardButton("💬 چت با هوش مصنوعی", callback_data='chat_ai')],
        [InlineKeyboardButton("📌 درباره من و همکاری با ما", callback_data='about')]
    ])
    await query.message.reply_text(translations[lang]['choose_option'], reply_markup=markup)
    return CHOOSE_OPTION

async def choose_option(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    lang = context.user_data.get('lang', 'fa')
    if query.data == 'about':
        await query.message.reply_text(translations[lang]['intro'])
        await query.message.reply_text(translations[lang]['ask_name'])
        return ASK_NAME
    await query.message.reply_text(translations[lang]['ai_wait'])
    return AI_CHAT

async def ai_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data.get('lang', 'fa')
    user_id = update.message.from_user.id
    if not can_send_message(user_id):
        await update.message.reply_text(translations[lang]['ai_limit_reached'])
        return AI_CHAT
    user_text = update.message.text
    increase_message_count(user_id)
    try:
        response = requests.post(HF_API_URL, headers=HEADERS, json={"inputs": user_text})
        if response.status_code == 200:
            data = response.json()
            reply = data[0]['generated_text'] if isinstance(data, list) and 'generated_text' in data[0] else "پاسخی دریافت نشد."
        else:
            reply = "خطا در دریافت پاسخ از مدل."
    except Exception:
        reply = "خطای ارتباط با هوش مصنوعی."
    await update.message.reply_text(reply)
    return AI_CHAT

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data.get('lang', 'fa')
    await update.message.reply_text(translations[lang]['cancel'])
    return ConversationHandler.END

def run_bot():
    app_tg = Application.builder().token(TOKEN).build()
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            ASK_LANGUAGE: [CallbackQueryHandler(choose_language)],
            CHOOSE_OPTION: [CallbackQueryHandler(choose_option)],
            AI_CHAT: [MessageHandler(filters.TEXT & ~filters.COMMAND, ai_chat)]
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        allow_reentry=True
    )
    app_tg.add_handler(conv_handler)
    app_tg.run_polling()

if __name__ == "__main__":
    app = Flask(__name__)

    @app.route('/')
    def ping():
        return 'pong'

    threading.Thread(target=lambda: app.run(host="0.0.0.0", port=8000)).start()
    run_bot()
