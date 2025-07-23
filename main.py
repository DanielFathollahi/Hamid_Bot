import os
from flask import Flask
from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup
)
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler, MessageHandler,
    ConversationHandler, ContextTypes, filters
)
from google.generativeai import GenerativeModel
from datetime import datetime

TOKEN = os.getenv("BOT_TOKEN")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

app = Flask(__name__)

LANGUAGE, MENU, ABOUT_JOB, ABOUT_PHONE, AI_CHAT = range(5)

languages = {
    "fa": {"flag": "🇮🇷", "name": "فارسی"},
    "en": {"flag": "🇬🇧", "name": "English"},
    "ar": {"flag": "🇸🇦", "name": "العربية"},
    "zh": {"flag": "🇨🇳", "name": "中文"}
}

about_us = {
    "fa": """📌 درباره من و همکاری با ما:

سلام و خوش‌آمدید 🌟

من حمید فتح‌اللهی هستم، فعال در حوزه تولید و عرضه انواع پیگمنت‌های معدنی قابل استفاده در:
🎨 سفال، سرامیک، فلز، شیشه و سیمان

🌏 واردکننده محصولات از کشورهای شرقی
🚢 صادرکننده به بازارهای عربی و غربی

✨ محصولات ما شامل:
🏗️ مصالح ساختمانی
🌱 محصولات کشاورزی
💎 مواد اولیه صنعت طلا
🖨️ جوهرهای چاپ دیجیتال
""",
    "en": """📌 About me & Cooperation:

Hello & welcome 🌟

I am Hamid Fathollahi, active in the production and supply of mineral pigments for:
🎨 Pottery, ceramics, metals, glass & cement

🌏 Importer from Eastern countries
🚢 Exporter to Arab & Western markets

✨ Our products include:
🏗️ Building materials
🌱 Agricultural products
💎 Gold industry raw materials
🖨️ Digital printing inks
""",
    "ar": """📌 عني والتعاون معنا:

مرحبًا بكم 🌟

أنا حميد فتح اللهي، ناشط في إنتاج وتوريد أصباغ معدنية تُستخدم في:
🎨 الفخار، السيراميك، المعادن، الزجاج والأسمنت

🌏 مستورد من الدول الشرقية
🚢 ومُصدر للأسواق العربية والغربية

✨ منتجاتنا تشمل:
🏗️ مواد البناء
🌱 المنتجات الزراعية
💎 مواد خام لصناعة الذهب
🖨️ وأحبار الطباعة الرقمية
""",
    "zh": """📌 关于我 & 合作:

欢迎 🌟

我是 Hamid Fathollahi，致力于生产和供应用于以下领域的矿物颜料：
🎨 陶瓷、金属、玻璃和水泥

🌏 从东方国家进口
🚢 向阿拉伯和西方市场出口

✨ 我们的产品包括：
🏗️ 建筑材料
🌱 农产品
💎 黄金行业原材料
🖨️ 数码印刷油墨
"""
}

ask_job = {
    "fa": "💼 لطفاً درباره کار خود توضیح دهید:",
    "en": "💼 Please describe your job:",
    "ar": "💼 من فضلك صف عملك:",
    "zh": "💼 请描述你的工作："
}

ask_phone = {
    "fa": "📱 لطفاً شماره تماس خود را ارسال کنید:",
    "en": "📱 Please send your phone number:",
    "ar": "📱 من فضلك أرسل رقم هاتفك:",
    "zh": "📱 请发送你的电话号码："
}

thank_you = {
    "fa": "✅ ممنون! 🔙 برای بازگشت /menu را بزنید",
    "en": "✅ Thank you! 🔙 To go back press /menu",
    "ar": "✅ شكرًا لك! 🔙 للعودة اضغط /menu",
    "zh": "✅ 谢谢你！🔙 返回请按 /menu"
}

back_menu = {
    "fa": "🔙 برای بازگشت /menu را بزنید",
    "en": "🔙 To go back press /menu",
    "ar": "🔙 للعودة اضغط /menu",
    "zh": "🔙 返回请按 /menu"
}

user_sessions = {}

@app.route('/')
def ping():
    return 'pong'

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    buttons = [
        [InlineKeyboardButton(f"{v['flag']} {v['name']}", callback_data=f"lang_{k}")]
        for k, v in languages.items()
    ]
    await update.message.reply_text("🌐 لطفاً زبان خود را انتخاب کنید:", reply_markup=InlineKeyboardMarkup(buttons))
    return LANGUAGE

async def set_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = update.callback_query.data.split("_")[1]
    context.user_data["lang"] = lang
    user_sessions[update.effective_user.id] = {"count": 0, "date": datetime.now().date()}
    await update.callback_query.answer()
    await show_menu(update, context)
    return MENU

async def show_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data["lang"]
    text = {
        "fa": "📋 لطفاً یکی را انتخاب کنید:",
        "en": "📋 Please choose an option:",
        "ar": "📋 الرجاء اختيار خيار:",
        "zh": "📋 请选择一个选项："
    }[lang]
    buttons = [
        [InlineKeyboardButton({"fa": "📄 درباره من و همکاری", "en": "📄 About me & Cooperation", "ar": "📄 عني والتعاون", "zh": "📄 关于我 & 合作"}[lang], callback_data="about")],
        [InlineKeyboardButton({"fa": "🤖 چت با هوش مصنوعی", "en": "🤖 Chat with AI", "ar": "🤖 الدردشة مع الذكاء الاصطناعي", "zh": "🤖 与AI聊天"}[lang], callback_data="ai_chat")]
    ]
    await update.callback_query.message.reply_text(text, reply_markup=InlineKeyboardMarkup(buttons))
    return MENU

async def about(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data["lang"]
    await update.callback_query.answer()
    await update.callback_query.message.reply_text(about_us[lang])
    await update.callback_query.message.reply_text(ask_job[lang])
    return ABOUT_JOB

async def about_job(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data["lang"]
    context.user_data["job_desc"] = update.message.text
    await update.message.reply_text(ask_phone[lang])
    return ABOUT_PHONE

async def about_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data["lang"]
    context.user_data["phone"] = update.message.text
    await update.message.reply_text(thank_you[lang])
    return MENU

async def ai_chat_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data["lang"]
    await update.callback_query.answer()
    await update.callback_query.message.reply_text(f"✍️ {back_menu[lang]}")
    return AI_CHAT

async def ai_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    lang = context.user_data["lang"]
    today = datetime.now().date()
    session = user_sessions.get(user_id)

    if session["date"] != today:
        session["count"] = 0
        session["date"] = today

    if session["count"] >= 5:
        await update.message.reply_text("🚫 " + {
            "fa": "شما امروز به ۵ پیام رسیدید.",
            "en": "You reached the 5 messages limit today.",
            "ar": "لقد وصلت إلى 5 رسائل اليوم.",
            "zh": "您今天已达到5条消息的限制。"
        }[lang])
        return AI_CHAT

    text = update.message.text.strip().lower()
    if "حمید فتح" in text or "hamid fathollahi" in text:
        await update.message.reply_text(about_us[lang])
        return AI_CHAT

    session["count"] += 1

    model = GenerativeModel("gemini-pro", api_key=GOOGLE_API_KEY)
    response = model.generate_content([update.message.text])
    answer = response.text.strip().split("\n")[0]

    await update.message.reply_text(f"🤖 {answer}")
    return AI_CHAT

async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    buttons = [
        [InlineKeyboardButton(f"{v['flag']} {v['name']}", callback_data=f"lang_{k}")]
        for k, v in languages.items()
    ]
    await update.message.reply_text("🌐 لطفاً زبان خود را انتخاب کنید:", reply_markup=InlineKeyboardMarkup(buttons))
    return LANGUAGE

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ گفتگو لغو شد.")
    return ConversationHandler.END

def main():
    app_tg = Application.builder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            LANGUAGE: [CallbackQueryHandler(set_language, pattern="^lang_")],
            MENU: [
                CallbackQueryHandler(about, pattern="^about$"),
                CallbackQueryHandler(ai_chat_start, pattern="^ai_chat$")
            ],
            ABOUT_JOB: [MessageHandler(filters.TEXT & ~filters.COMMAND, about_job)],
            ABOUT_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, about_phone)],
            AI_CHAT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, ai_chat),
                CommandHandler("menu", menu)
            ]
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )

    app_tg.add_handler(conv_handler)
    app_tg.run_polling()

if __name__ == "__main__":
    import threading
    threading.Thread(target=lambda: app.run(host="0.0.0.0", port=8000)).start()
    main()
