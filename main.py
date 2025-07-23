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

ASK_LANGUAGE, ASK_DESCRIPTION, ASK_PHONE = range(3)

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
        'desc': "لطفاً درباره کار خود و خودتان توضیح دهید ✍️",
        'phone': "لطفاً شماره تلفن خود را ارسال کنید 📱",
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
        'desc': "Please describe yourself and your work ✍️",
        'phone': "Please send your phone number 📱",
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
        'desc': "يرجى تقديم نفسك وعملك ✍️",
        'phone': "يرجى إرسال رقم هاتفك 📱",
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
        'desc': "请介绍一下您自己和您的工作 ✍️",
        'phone': "请发送您的电话号码 📱",
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

async def collect(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data.get('lang', 'fa')
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
                MessageHandler(filters.CONTACT, collect),
                MessageHandler(filters.TEXT & ~filters.COMMAND, collect)
            ]
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        allow_reentry=True
    )
    app_tg.add_handler(conv_handler)
    app_tg.run_polling()

if __name__ == "__main__":
    threading.Thread(target=lambda: app.run(host="0.0.0.0", port=8000)).start()
    run_bot()
