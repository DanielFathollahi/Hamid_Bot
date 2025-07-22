import os
import threading
from datetime import date
from flask import Flask
from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup,
    KeyboardButton, ReplyKeyboardMarkup
)
from telegram.ext import (
    Application, CommandHandler, MessageHandler, CallbackQueryHandler,
    ConversationHandler, ContextTypes, filters
)
import google.generativeai as genai

# تنظیم Google Gemini
genai.configure(api_key=os.environ["GOOGLE_API_KEY"])
model = genai.GenerativeModel("gemini-1.5-flash")

GROUP_CHAT_ID = -1002542201765
ASK_DESCRIPTION, ASK_PHONE = range(2)

app = Flask(__name__)

@app.route('/')
def ping():
    return 'pong'


# متون به ۴ زبان (fa, en, ar, zh)
TEXTS = {
    "lang_select": {
        "fa": "🌐 لطفاً زبان خود را انتخاب کنید:",
        "en": "🌐 Please select your language:",
        "ar": "🌐 يرجى اختيار لغتك:",
        "zh": "🌐 请选择您的语言："
    },
    "options": {
        "fa": ["📄 درباره من و همکاری با ما", "🤖 چت با هوش مصنوعی"],
        "en": ["📄 About Me and Collaboration", "🤖 Chat with AI"],
        "ar": ["📄 عني والتعاون معنا", "🤖 الدردشة مع الذكاء الاصطناعي"],
        "zh": ["📄 关于我和合作", "🤖 与AI聊天"]
    },
    "intro_about": {
        "fa": """
📌 معرفی: حمید فتح‌اللهی

سلام و خوش‌آمدید 🌟

من حمید فتح‌اللهی هستم، فعال در حوزه تولید و عرضه انواع پیگمنت‌های معدنی قابل استفاده در:
🎨 سفال، سرامیک، فلز، شیشه و سیمان

🌏 واردکننده محصولات از کشورهای شرقی
🚢 صادرکننده به بازارهای عربی و غربی

✨ محصولات ما شامل:
🏗️ مصالح ساختمانی
🌱 محصولات کشاورزی
💎 مواد اولیه صنعت طلا
""",
        "en": """
📌 Introduction: Hamid Fathollahi

Hello and welcome 🌟

I am Hamid Fathollahi, active in production and supply of various mineral pigments usable in:
🎨 Pottery, ceramics, metal, glass, and cement

🌏 Importer of products from Eastern countries
🚢 Exporter to Arab and Western markets

✨ Our products include:
🏗️ Construction materials
🌱 Agricultural products
💎 Raw materials for the gold industry
""",
        "ar": """
📌 مقدمة: حميد فتح اللهي

مرحباً بكم 🌟

أنا حميد فتح اللهي، نشط في إنتاج وتوريد أنواع مختلفة من الأصباغ المعدنية المستخدمة في:
🎨 الفخار، السيراميك، المعادن، الزجاج، والأسمنت

🌏 مستورد منتجات من الدول الشرقية
🚢 مصدّر إلى الأسواق العربية والغربية

✨ تشمل منتجاتنا:
🏗️ مواد البناء
🌱 المنتجات الزراعية
💎 المواد الخام لصناعة الذهب
""",
        "zh": """
📌 介绍：哈米德·法索拉希

您好，欢迎光临 🌟

我是一名活跃于生产和供应各种矿物颜料的哈米德·法索拉希，这些颜料可用于：
🎨 陶器、陶瓷、金属、玻璃和水泥

🌏 从东方国家进口产品
🚢 出口到阿拉伯和西方市场

✨ 我们的产品包括：
🏗️ 建筑材料
🌱 农产品
💎 黄金行业的原材料
"""
    },
    "ask_description": {
        "fa": "✍️ لطفاً درباره‌ی کار خود و خودتان توضیح دهید:",
        "en": "✍️ Please describe your work and yourself:",
        "ar": "✍️ يرجى وصف عملك ونفسك:",
        "zh": "✍️ 请描述您的工作和您自己："
    },
    "ask_phone": {
        "fa": "📞 لطفاً شماره تلفن خود را ارسال کنید:",
        "en": "📞 Please send your phone number:",
        "ar": "📞 يرجى إرسال رقم هاتفك:",
        "zh": "📞 请发送您的电话号码："
    },
    "info_received": {
        "fa": "✅ اطلاعات شما ثبت شد. ممنون 🙏",
        "en": "✅ Your information has been recorded. Thank you 🙏",
        "ar": "✅ تم تسجيل معلوماتك. شكراً 🙏",
        "zh": "✅ 您的信息已被记录。谢谢 🙏"
    },
    "chat_limit_reached": {
        "fa": "🚫 شما به حداکثر تعداد پیام‌های مجاز امروز (۵ پیام) رسیدید.",
        "en": "🚫 You have reached the maximum allowed messages for today (5 messages).",
        "ar": "🚫 لقد وصلت إلى الحد الأقصى للرسائل المسموح بها اليوم (5 رسائل).",
        "zh": "🚫 您已达到今天允许的最大消息数（5条消息）。"
    },
    "chat_prompt": {
        "fa": "🤖 می‌توانید تا ۵ پیام در روز با هوش مصنوعی چت کنید. سوال خود را بپرسید:",
        "en": "🤖 You can chat with AI up to 5 messages per day. Please ask your question:",
        "ar": "🤖 يمكنك الدردشة مع الذكاء الاصطناعي حتى 5 رسائل في اليوم. يرجى طرح سؤالك:",
        "zh": "🤖 您每天最多可与AI聊天5条消息。请提出您的问题："
    },
    "token_denied": {
        "fa": "❌ اجازه ندارم در این مورد صحبت کنم.",
        "en": "❌ I'm not allowed to discuss this.",
        "ar": "❌ لا يسمح لي بالتحدث عن هذا.",
        "zh": "❌ 我不允许讨论此事。"
    },
    "back_to_main": {
        "fa": "🏠 بازگشت به منوی اصلی",
        "en": "🏠 Back to main menu",
        "ar": "🏠 العودة إلى القائمة الرئيسية",
        "zh": "🏠 返回主菜单"
    },
    "back_to_main_prompt": {
        "fa": "برای بازگشت به منوی اصلی اینجا کلیک کنید:",
        "en": "Click here to return to the main menu:",
        "ar": "انقر هنا للعودة إلى القائمة الرئيسية:",
        "zh": "点击这里返回主菜单："
    }
}

def get_text(key, lang):
    return TEXTS.get(key, {}).get(lang, TEXTS.get(key, {}).get("fa", ""))


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("فارسی", callback_data="lang_fa")],
        [InlineKeyboardButton("English", callback_data="lang_en")],
        [InlineKeyboardButton("العربية", callback_data="lang_ar")],
        [InlineKeyboardButton("中文", callback_data="lang_zh")]
    ]
    if update.callback_query:
        query = update.callback_query
        await query.answer()
        await query.message.reply_text(
            get_text("lang_select", context.user_data.get("lang", "fa")),
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    else:
        await update.message.reply_text(
            get_text("lang_select", context.user_data.get("lang", "fa")),
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

async def language_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    lang = query.data.split("_")[1]
    context.user_data["lang"] = lang

    options = get_text("options", lang)
    keyboard = [
        [InlineKeyboardButton(options[0], callback_data="about_us")],
        [InlineKeyboardButton(options[1], callback_data="chat_ai")]
    ]
    await query.message.reply_text(
        "👇 " + ({"fa": "یکی از گزینه‌های زیر را انتخاب کنید:", "en": "Please choose one of the options below:",
                 "ar": "يرجى اختيار أحد الخيارات أدناه:", "zh": "请选择以下选项之一："}[lang]),
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def about_us(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    lang = context.user_data.get("lang", "fa")

    await query.message.reply_text(get_text("intro_about", lang))
    await query.message.reply_text(get_text("ask_description", lang))
    return ASK_DESCRIPTION

async def ask_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["description"] = update.message.text
    lang = context.user_data.get("lang", "fa")
    keyboard = [[KeyboardButton("📱 " + ({"fa": "ارسال شماره", "en": "Send Phone", "ar": "إرسال الرقم", "zh": "发送号码"}[lang]), request_contact=True)]]
    markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    await update.message.reply_text(get_text("ask_phone", lang), reply_markup=markup)
    return ASK_PHONE

async def collect(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    contact = update.message.contact
    phone = contact.phone_number if contact else update.message.text
    description = context.user_data.get("description", "")
    lang = context.user_data.get("lang", "fa")

    msg = (
        f"👤 {user.first_name} {user.last_name or ''}\n"
        f"🆔 {user.id}\n"
        f"🔗 @{user.username or 'ندارد'}\n"
        f"📝 {description}\n"
        f"📞 {phone}"
    )

    await context.bot.send_message(GROUP_CHAT_ID, msg)
    await update.message.reply_text(get_text("info_received", lang), reply_markup=ReplyKeyboardMarkup([], resize_keyboard=True))
    return ConversationHandler.END


def reset_ai_counter_if_new_day(context):
    user_data = context.user_data
    today_str = date.today().isoformat()
    if user_data.get("last_chat_day") != today_str:
        user_data["last_chat_day"] = today_str
        user_data["ai_count"] = 0

async def chat_ai_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    reset_ai_counter_if_new_day(context)
    lang = context.user_data.get("lang", "fa")

    await query.message.reply_text(get_text("chat_prompt", lang))

async def chat_ai(update: Update, context: ContextTypes.DEFAULT_TYPE):
    reset_ai_counter_if_new_day(context)
    count = context.user_data.get("ai_count", 0)
    lang = context.user_data.get("lang", "fa")

    if count >= 5:
        await update.message.reply_text(get_text("chat_limit_reached", lang))
        return

    text = update.message.text.lower()

    # همه حالات درباره حمید فتح اللهی به همه زبان‌ها
    trigger_phrases = {
        "fa": ["حمید فتح اللهی کیه", "حمید فتح اللهی کیست", "درباره حمید فتح اللهی"],
        "en": ["who is hamid fathollahi", "about hamid fathollahi"],
        "ar": ["من هو حميد فتح اللهي", "عن حميد فتح اللهي"],
        "zh": ["谁是哈米德·法索拉希", "关于哈米德·法索拉希"]
    }

    if any(phrase in text for phrase in trigger_phrases.get(lang, []) + sum(trigger_phrases.values(), [])):
        await update.message.reply_text(get_text("intro_about", lang))
        return

    if "توکن" in text or "token" in text:
        await update.message.reply_text(get_text("token_denied", lang))
        return

    context.user_data["ai_count"] = count + 1

    # پاسخ هوش مصنوعی
    response = model.start_chat().send_message(update.message.text)
    await update.message.reply_text(response.text)

    keyboard = [
        [InlineKeyboardButton(get_text("back_to_main", lang), callback_data="back_to_main")]
    ]
    await update.message.reply_text(get_text("back_to_main_prompt", lang), reply_markup=InlineKeyboardMarkup(keyboard))


async def back_to_main(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await start(update, context)

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("لغو شد.")
    return ConversationHandler.END


def run_bot():
    app_tg = Application.builder().token(os.environ["TOKEN"]).build()

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
    app_tg.add_handler(CallbackQueryHandler(language_selected, pattern="^lang_"))
    app_tg.add_handler(CallbackQueryHandler(about_us, pattern="about_us"))
    app_tg.add_handler(CallbackQueryHandler(chat_ai_start, pattern="chat_ai"))
    app_tg.add_handler(CallbackQueryHandler(back_to_main, pattern="back_to_main"))
    app_tg.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat_ai))

    app_tg.run_polling()


if __name__ == "__main__":
    threading.Thread(target=lambda: app.run(host="0.0.0.0", port=8000)).start()
    run_bot()
