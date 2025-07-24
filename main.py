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

ASK_LANGUAGE, ASK_NAME, ASK_JOB, ASK_PHONE, ASK_EMAIL = range(5)

# مسیر فایل‌های صوتی
voice_files = {
    'fa': 'معرفی من به زبان فارسی.ogg',
    'en': 'My information is in English.ogg',
    'ar': 'معلوماتي باللغة العربي.ogg',
    'zh': '我的信息是中文的.ogg'
}

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
        'ask_name': "لطفاً نام و نام خانوادگی خود را وارد کنید ✍️",
        'ask_job': "لطفاً اطلاعات شغلی خود را بنویسید ✍️",
        'ask_phone': "لطفاً شماره تلفن خود را ارسال کنید 📱",
        'ask_email': "لطفاً ایمیل خود را وارد کنید 📧",
        'thanks': "✅ اطلاعات شما ثبت شد. ممنون 🙏",
        'cancel': "لغو شد."
    },
    'en': {
        'intro': """
📌 About Me & Cooperation:

Hello and welcome 🌟

I am Hamid Fathollahi, active in the production and supply of various mineral pigments used in:
🎨 pottery, ceramics, metals, glass, and cement

Also:
🌏 Importer from eastern countries
🚢 Exporter to Arab and Western markets

✨ Our products include a wide range of:
🏗️ building materials
🌱 agricultural products
💎 raw materials for the gold industry
🖨️ and digital printing inks
""",
        'ask_name': "Please enter your full name ✍️",
        'ask_job': "Please describe your job or business ✍️",
        'ask_phone': "Please send your phone number 📱",
        'ask_email': "Please enter your email address 📧",
        'thanks': "✅ Your information has been recorded. Thank you 🙏",
        'cancel': "Cancelled."
    },
    'ar': {
        'intro': """
📌 عني والتعاون معنا:

مرحبًا بكم 🌟

أنا حميد فتح‌اللهي، ناشط في إنتاج وتوريد أصباغ معدنية متنوعة تُستخدم في:
🎨 الفخار، السيراميك، المعادن، الزجاج والإسمنت

وأيضًا:
🌏 مستورد من الدول الشرقية
🚢 ومصدر للأسواق العربية والغربية

✨ تشمل منتجاتنا مجموعة واسعة من:
🏗️ مواد البناء
🌱 المنتجات الزراعية
💎 المواد الخام لصناعة الذهب
🖨️ وأحبار الطباعة الرقمية
""",
        'ask_name': "يرجى إدخال الاسم الكامل ✍️",
        'ask_job': "يرجى وصف عملك أو مهنتك ✍️",
        'ask_phone': "يرجى إرسال رقم الهاتف 📱",
        'ask_email': "يرجى إدخال البريد الإلكتروني 📧",
        'thanks': "✅ تم تسجيل معلوماتك. شكرًا 🙏",
        'cancel': "تم الإلغاء."
    },
    'zh': {
        'intro': """
📌 关于我与合作：

您好，欢迎 🌟

我是 Hamid Fathollahi，活跃于各种矿物颜料的生产和供应，这些颜料可用于：
🎨 陶瓷、陶器、金属、玻璃和水泥

此外：
🌏 从东方国家进口
🚢 向阿拉伯和西方市场出口

✨ 我们的产品包括广泛的：
🏗️ 建筑材料
🌱 农产品
💎 黄金工业的原材料
🖨️ 以及数码印刷油墨
""",
        'ask_name': "请输入您的全名 ✍️",
        'ask_job': "请输入您的职业信息 ✍️",
        'ask_phone': "请发送您的电话号码 📱",
        'ask_email': "请输入您的电子邮件地址 📧",
        'thanks': "✅ 您的信息已记录。谢谢 🙏",
        'cancel': "已取消。"
    }
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

    # ارسال فایل صوتی معرفی با توجه به زبان
    voice_path = voice_files.get(lang)
    if voice_path and os.path.exists(voice_path):
        with open(voice_path, 'rb') as voice:
            await query.message.reply_voice(voice)

    # ارسال پیام معرفی متنی و سوال اول
    await query.message.reply_text(translations[lang]['intro'])
    await query.message.reply_text(translations[lang]['ask_name'])
    return ASK_NAME

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
            ASK_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_job)],
            ASK_JOB: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_phone)],
            ASK_PHONE: [
                MessageHandler(filters.CONTACT, ask_email),
                MessageHandler(filters.TEXT & ~filters.COMMAND, ask_email)
            ],
            ASK_EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, collect)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        allow_reentry=True
    )
    app_tg.add_handler(conv_handler)
    app_tg.run_polling()

if __name__ == "__main__":
    threading.Thread(target=lambda: app.run(host="0.0.0.0", port=8000)).start()
    run_bot()
