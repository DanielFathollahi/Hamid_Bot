import os
import threading
from datetime import datetime, timedelta
from telegram import (
    Update, KeyboardButton, ReplyKeyboardMarkup,
    InlineKeyboardButton, InlineKeyboardMarkup
)
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler, MessageHandler,
    ConversationHandler, ContextTypes, filters
)
import openai
import asyncio

TOKEN = os.getenv("TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")  # کلید API اوپن‌ای‌آی خودت
GROUP_CHAT_ID = -1002542201765

openai.api_key = OPENAI_API_KEY

app = None  # flask app را اینجا می‌گذاری اگر نیاز داری

# وضعیت‌ها
ASK_LANGUAGE, CHOOSE_OPTION, ASK_NAME, ASK_JOB, ASK_PHONE, ASK_EMAIL, AI_CHAT = range(7)

# دیکشنری برای محدودیت پیام روزانه چت AI
user_daily_usage = {}

# تابع برای چک کردن محدودیت ۵ پیام در روز
def can_send_message(user_id):
    today = datetime.now().date()
    if user_id in user_daily_usage:
        last_date, count = user_daily_usage[user_id]
        if last_date == today:
            return count < 5
        else:
            user_daily_usage[user_id] = (today, 0)
            return True
    else:
        user_daily_usage[user_id] = (today, 0)
        return True

def increase_message_count(user_id):
    today = datetime.now().date()
    if user_id in user_daily_usage:
        last_date, count = user_daily_usage[user_id]
        if last_date == today:
            user_daily_usage[user_id] = (today, count + 1)
        else:
            user_daily_usage[user_id] = (today, 1)
    else:
        user_daily_usage[user_id] = (today, 1)

translations = {
    # همون دیکشنری ترجمه که خودت داری
    'fa': {
        'intro': """
📌 درباره من و همکاری با ما:

سلام و خوش‌آمدید 🌟

من حمید فتح‌اللهی هستم، فعال در حوزه تولید و عرضه انواع پیگمنت‌های معدنی قابل استفاده در:
🎨 سفال، سرامیک، فلز، شیشه و سیمان

همچنین:
🌏 واردکننده محصولات از کشورهای شرقی
🚢 صادرکننده به بازارهای عربی و غربی

✨ محصولات ما شامل طیف گسترده‌ای از:
🏗️ مصالح ساختمانی
🌱 محصولات کشاورزی
💎 مواد اولیه صنعت طلا
🖨️ و جوهرهای چاپ دیجیتال
""",
        'ask_name': "لطفاً نام و نام خانوادگی خود را وارد کنید ✍️",
        'ask_job': "لطفاً اطلاعات شغلی خود را بنویسید ✍️",
        'ask_phone': "لطفاً شماره تلفن خود را ارسال کنید 📱",
        'ask_email': "لطفاً ایمیل خود را وارد کنید 📧",
        'thanks': "✅ اطلاعات شما ثبت شد. ممنون 🙏",
        'cancel': "لغو شد.",
        'choose_option': "لطفاً یکی از گزینه‌های زیر را انتخاب کنید:",
        'ai_limit_reached': "❌ شما امروز به حد مجاز ۵ پیام چت با هوش مصنوعی رسیدید. لطفاً فردا دوباره تلاش کنید.",
        'ai_wait': "در حال پردازش پاسخ هوش مصنوعی، لطفاً صبر کنید...",
    },
    # ترجمه انگلیسی و سایر زبان‌ها هم اضافه کن مشابه قبلی
    'en': {
        'intro': "📌 About Me & Cooperation: ...",  # کامل کن مثل قبلی
        'ask_name': "Please enter your full name ✍️",
        'ask_job': "Please describe your job or business ✍️",
        'ask_phone': "Please send your phone number 📱",
        'ask_email': "Please enter your email address 📧",
        'thanks': "✅ Your information has been recorded. Thank you 🙏",
        'cancel': "Cancelled.",
        'choose_option': "Please choose one of the options below:",
        'ai_limit_reached': "❌ You have reached your daily limit of 5 AI chat messages. Please try again tomorrow.",
        'ai_wait': "Waiting for AI response, please wait...",
    },
    # زبان‌های ar و zh را هم مثل قبلی اضافه کن
}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    keyboard = [
        [
            InlineKeyboardButton("🇮🇷 فارسی", callback_data='fa'),
            InlineKeyboardButton("🇬🇧 English", callback_data='en')
        ],
        [
            InlineKeyboardButton("🇸🇦 العربية", callback_data='ar'),
            InlineKeyboardButton("🇨🇳 中文", callback_data='zh')
        ]
    ]
    markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("لطفاً زبان خود را انتخاب کنید 🌐", reply_markup=markup)
    return ASK_LANGUAGE

async def choose_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    lang = query.data
    context.user_data['lang'] = lang

    # نمایش گزینه‌ها به کاربر
    keyboard = [
        [InlineKeyboardButton("💬 چت با هوش مصنوعی", callback_data='chat_ai')],
        [InlineKeyboardButton("📌 درباره من و همکاری با ما", callback_data='about')]
    ]
    markup = InlineKeyboardMarkup(keyboard)
    await query.message.reply_text(translations[lang]['choose_option'], reply_markup=markup)

    return CHOOSE_OPTION

async def choose_option(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    choice = query.data
    lang = context.user_data.get('lang', 'fa')

    if choice == 'about':
        await query.message.reply_text(translations[lang]['intro'])
        await query.message.reply_text(translations[lang]['ask_name'])
        return ASK_NAME
    elif choice == 'chat_ai':
        await query.message.reply_text(translations[lang]['ai_wait'])
        return AI_CHAT

async def ask_job(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data.get('lang', 'fa')
    context.user_data["full_name"] = update.message.text
    await update.message.reply_text(translations[lang]['ask_job'], reply_markup=ReplyKeyboardMarkup([['/cancel']], one_time_keyboard=True, resize_keyboard=True))
    return ASK_JOB

async def ask_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data.get('lang', 'fa')
    context.user_data["job_info"] = update.message.text
    keyboard = [[KeyboardButton("📱 ارسال شماره", request_contact=True)], ['/cancel']]
    markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    await update.message.reply_text(translations[lang]['ask_phone'], reply_markup=markup)
    return ASK_PHONE

async def ask_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data.get('lang', 'fa')
    contact = update.message.contact
    phone = contact.phone_number if contact else update.message.text
    context.user_data["phone"] = phone
    await update.message.reply_text(translations[lang]['ask_email'], reply_markup=ReplyKeyboardMarkup([['/cancel']], one_time_keyboard=True, resize_keyboard=True))
    return ASK_EMAIL

async def collect(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data.get('lang', 'fa')
    user = update.message.from_user
    email = update.message.text
    context.user_data["email"] = email

    full_name = context.user_data.get("full_name", "")
    job_info = context.user_data.get("job_info", "")
    phone = context.user_data.get("phone", "")

    msg = (
        f"👤 نام و نام خانوادگی: {full_name}\n"
        f"📝 اطلاعات شغلی: {job_info}\n"
        f"📞 شماره تماس: {phone}\n"
        f"📧 ایمیل: {email}\n"
        f"🆔 آیدی: {user.id}\n"
        f"🔗 نام کاربری: @{user.username or 'ندارد'}"
    )

    await context.bot.send_message(GROUP_CHAT_ID, msg)
    await update.message.reply_text(translations[lang]['thanks'], reply_markup=ReplyKeyboardMarkup([['/start']], resize_keyboard=True))
    return ConversationHandler.END

async def ai_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data.get('lang', 'fa')
    user_id = update.message.from_user.id

    if not can_send_message(user_id):
        await update.message.reply_text(translations[lang]['ai_limit_reached'])
        return AI_CHAT  # می‌تونی اینجا Conversation را بسته یا باز نگه داری

    user_text = update.message.text
    increase_message_count(user_id)

    try:
        # ارسال درخواست به OpenAI
        response = openai.Completion.create(
            engine="text-davinci-003",  # یا مدل دلخواه خودت
            prompt=user_text,
            max_tokens=150,
            n=1,
            stop=None,
            temperature=0.7,
        )
        answer = response.choices[0].text.strip()
    except Exception as e:
        answer = "خطایی در پاسخ هوش مصنوعی رخ داده است."

    await update.message.reply_text(answer)
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
            ASK_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_job)],
            ASK_JOB: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_phone)],
            ASK_PHONE: [
                MessageHandler(filters.CONTACT, ask_email),
                MessageHandler(filters.TEXT & ~filters.COMMAND, ask_email)
            ],
            ASK_EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, collect)],
            AI_CHAT: [MessageHandler(filters.TEXT & ~filters.COMMAND, ai_chat)]
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        allow_reentry=True
    )
    app_tg.add_handler(conv_handler)
    app_tg.run_polling()

if __name__ == "__main__":
    import threading
    from flask import Flask

    app = Flask(__name__)

    @app.route('/')
    def ping():
        return 'pong'

    threading.Thread(target=lambda: app.run(host="0.0.0.0", port=8000)).start()
    run_bot()
