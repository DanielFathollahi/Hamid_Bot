import os
import threading
from flask import Flask
from telegram import (
    Update, KeyboardButton, ReplyKeyboardMarkup,
    InlineKeyboardButton, InlineKeyboardMarkup
)
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler, MessageHandler,
    ConversationHandler, ContextTypes, filters
)

TOKEN = os.getenv("TOKEN")
GROUP_CHAT_ID = -1002542201765

app = Flask(__name__)

@app.route('/')
def ping():
    return 'pong'

ASK_LANGUAGE, ASK_DESCRIPTION, ASK_PHONE, ASK_EMAIL, ASK_JOB = range(5)

translations = {
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
        'desc': "لطفاً درباره کار خود توضیح دهید ✍️",
        'phone': "شماره تماس خود را ارسال کنید یا دکمه زیر را بزنید 📱",
        'email': "لطفاً ایمیل خود را وارد کنید 📧",
        'job': "شغل یا زمینه فعالیت خود را وارد کنید 💼",
        'thanks': "✅ اطلاعات شما ثبت شد. ممنون 🙏",
        'cancel': "لغو شد."
    },
    'en': {
        'intro': "📌 About Me & Cooperation:\n\nWelcome 🌟...",
        'desc': "Please describe your work ✍️",
        'phone': "Send your phone number or click the button 📱",
        'email': "Please enter your email 📧",
        'job': "Enter your job or business field 💼",
        'thanks': "✅ Your information was saved. Thank you 🙏",
        'cancel': "Cancelled."
    }
    # Add other languages if needed
}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    keyboard = [
        [InlineKeyboardButton("🇮🇷 فارسی", callback_data='fa')],
        [InlineKeyboardButton("🇬🇧 English", callback_data='en')],
    ]
    markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("لطفاً زبان خود را انتخاب کنید 🌐", reply_markup=markup)
    return ASK_LANGUAGE

async def choose_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    lang = query.data
    context.user_data['lang'] = lang

    await query.message.reply_text(translations[lang]['intro'])
    await query.message.reply_text(translations[lang]['desc'])
    return ASK_DESCRIPTION

async def ask_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data.get('lang', 'fa')
    context.user_data["description"] = update.message.text

    keyboard = [[KeyboardButton("📱 ارسال شماره", request_contact=True)]]
    markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    await update.message.reply_text(translations[lang]['phone'], reply_markup=markup)
    return ASK_PHONE

async def ask_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data.get('lang', 'fa')
    contact = update.message.contact
    context.user_data["phone"] = contact.phone_number if contact else update.message.text
    await update.message.reply_text(translations[lang]['email'])
    return ASK_EMAIL

async def ask_job(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data.get('lang', 'fa')
    context.user_data["email"] = update.message.text
    await update.message.reply_text(translations[lang]['job'])
    return ASK_JOB

async def collect(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data.get('lang', 'fa')
    user = update.message.from_user

    context.user_data["job"] = update.message.text

    first_name = user.first_name or ''
    last_name = user.last_name or ''
    username = user.username or 'ندارد'
    user_id = user.id
    description = context.user_data.get("description", "")
    phone = context.user_data.get("phone", "نامشخص")
    email = context.user_data.get("email", "نامشخص")
    job = context.user_data.get("job", "نامشخص")

    msg = (
        f"📥 درخواست همکاری جدید:\n\n"
        f"👤 نام: {first_name} {last_name}\n"
        f"🆔 آیدی عددی: {user_id}\n"
        f"🔗 یوزرنیم: @{username}\n"
        f"📞 شماره تماس: {phone}\n"
        f"📧 ایمیل: {email}\n"
        f"💼 شغل: {job}\n"
        f"📝 توضیحات: {description}"
    )

    await context.bot.send_message(GROUP_CHAT_ID, msg)
    await update.message.reply_text(translations[lang]['thanks'])
    return ConversationHandler.END

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
            ASK_DESCRIPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_phone)],
            ASK_PHONE: [
                MessageHandler(filters.CONTACT, ask_email),
                MessageHandler(filters.TEXT & ~filters.COMMAND, ask_email)
            ],
            ASK_EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_job)],
            ASK_JOB: [MessageHandler(filters.TEXT & ~filters.COMMAND, collect)]
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        allow_reentry=True
    )
    app_tg.add_handler(conv_handler)
    app_tg.run_polling()

if __name__ == "__main__":
    threading.Thread(target=lambda: app.run(host="0.0.0.0", port=8000)).start()
    run_bot()
