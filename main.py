import os
from flask import Flask
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, filters,
    ContextTypes, ConversationHandler
)
from google.generativeai import GenerativeModel

import asyncio

# 📌 مرحله‌های گفتگو
LANGUAGE, MENU, COLLECT_NAME, COLLECT_JOB, COLLECT_PHONE, COLLECT_EMAIL, CHAT_AI = range(7)

# 🌍 زبان‌ها
LANGUAGES = {
    "🇮🇷 فارسی": "fa",
    "🇬🇧 English": "en",
    "🇸🇦 العربية": "ar",
    "🇨🇳 中文": "zh"
}

# پیام‌های ترجمه‌شده
TEXTS = {
    "menu": {
        "fa": "لطفاً یکی از گزینه‌ها را انتخاب کنید:",
        "en": "Please choose an option:",
        "ar": "يرجى اختيار خيار:",
        "zh": "请选择一个选项："
    },
    "about": {
        "fa": "📌 معرفی: حمید فتح‌اللهی\n\nسلام و خوش‌آمدید 🌟\n\n"
              "من حمید فتح‌اللهی هستم، فعال در حوزه تولید و عرضه انواع پیگمنت‌های معدنی قابل استفاده در:\n"
              "🎨 سفال، سرامیک، فلز، شیشه و سیمان\n\n"
              "همچنین:\n🌏 واردکننده محصولات از کشورهای شرقی\n🚢 صادرکننده به بازارهای عربی و غربی\n\n"
              "✨ محصولات ما شامل طیف گسترده‌ای از:\n🏗️ مصالح ساختمانی\n🌱 محصولات کشاورزی\n💎 مواد اولیه صنعت طلا\n🖋️ جوهرهای چاپ دیجیتال",
        "en": "📌 Introduction: Hamid Fathollahi\n\nWelcome 🌟\n\n"
              "I am Hamid Fathollahi, active in producing and supplying various mineral pigments used in:\n"
              "🎨 Pottery, ceramics, metal, glass, and cement\n\n"
              "Also:\n🌏 Importer from eastern countries\n🚢 Exporter to Arab and Western markets\n\n"
              "✨ Our products include a wide range of:\n🏗️ Building materials\n🌱 Agricultural products\n💎 Raw materials for the gold industry\n🖋️ Digital printing inks",
        "ar": "📌 تقديم: حميد فتح‌اللهي\n\nمرحبًا بكم 🌟\n\n"
              "أنا حميد فتح‌اللهي، ناشط في إنتاج وتوريد أصباغ معدنية متنوعة تُستخدم في:\n"
              "🎨 الفخار، السيراميك، المعادن، الزجاج، والإسمنت\n\n"
              "كذلك:\n🌏 مستورد من الدول الشرقية\n🚢 مُصدّر للأسواق العربية والغربية\n\n"
              "✨ تشمل منتجاتنا مجموعة واسعة من:\n🏗️ مواد البناء\n🌱 المنتجات الزراعية\n💎 المواد الخام لصناعة الذهب\n🖋️ أحبار الطباعة الرقمية",
        "zh": "📌 介绍：哈米德·法索拉希\n\n欢迎 🌟\n\n"
              "我是哈米德·法索拉希，活跃于生产和供应各种用于以下领域的矿物颜料：\n"
              "🎨 陶器、陶瓷、金属、玻璃和水泥\n\n"
              "此外：\n🌏 从东方国家进口\n🚢 出口到阿拉伯和西方市场\n\n"
              "✨ 我们的产品涵盖广泛：\n🏗️ 建筑材料\n🌱 农产品\n💎 黄金工业的原材料\n🖋️ 数码印刷油墨"
    },
    "back": {
        "fa": "برای بازگشت به منو، /menu را بزنید.",
        "en": "To return to the menu, press /menu.",
        "ar": "للعودة إلى القائمة اضغط /menu.",
        "zh": "要返回菜单，请按 /menu。"
    }
}

GROUP_ID = -1002542201765

app = Flask(__name__)
users = {}

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
model = GenerativeModel("gemini-pro", api_key=GOOGLE_API_KEY)

@app.route('/')
def home():
    return 'OK', 200


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = [[KeyboardButton(l) for l in LANGUAGES]]
    await update.message.reply_text(
        "🌐 زبان/Language/لغة/语言:", 
        reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True)
    )
    return LANGUAGE


async def set_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = LANGUAGES.get(update.message.text)
    if not lang:
        return LANGUAGE
    context.user_data['lang'] = lang
    context.user_data['chats'] = 0
    kb = [[
        KeyboardButton("📄 درباره من و همکاری با ما"),
        KeyboardButton("🤖 چت با هوش مصنوعی")
    ]]
    await update.message.reply_text(
        TEXTS["menu"][lang],
        reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True)
    )
    return MENU


async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    return await set_language(update, context)


async def about_me(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data['lang']
    await update.message.reply_text(TEXTS["about"][lang])
    await update.message.reply_text("👤 لطفاً نام و نام خانوادگی‌تان را وارد کنید:", reply_markup=ReplyKeyboardRemove())
    return COLLECT_NAME


async def collect_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['name'] = update.message.text
    await update.message.reply_text("💼 لطفاً درباره شغل خود توضیح دهید:")
    return COLLECT_JOB


async def collect_job(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['job'] = update.message.text
    await update.message.reply_text("📱 لطفاً شماره تماس خود را وارد کنید:")
    return COLLECT_PHONE


async def collect_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['phone'] = update.message.text
    await update.message.reply_text("📧 لطفاً ایمیل خود را وارد کنید:")
    return COLLECT_EMAIL


async def collect_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['email'] = update.message.text

    info = (
        f"👤 نام: {context.user_data['name']}\n"
        f"💼 شغل: {context.user_data['job']}\n"
        f"📱 شماره: {context.user_data['phone']}\n"
        f"📧 ایمیل: {context.user_data['email']}"
    )

    await context.bot.send_message(chat_id=GROUP_ID, text=info)
    lang = context.user_data['lang']
    await update.message.reply_text(TEXTS["back"][lang])
    return MENU


async def chat_ai(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data['lang']
    if context.user_data['chats'] >= 5:
        await update.message.reply_text("⛔ به سقف ۵ پیام در روز رسیده‌اید.")
        return MENU

    text = update.message.text.strip()
    if "حمید فتح‌اللهی" in text or "Hamid Fathollahi" in text:
        await update.message.reply_text(TEXTS["about"][lang])
        return MENU

    context.user_data['chats'] += 1
    resp = model.generate_content(text).text
    await update.message.reply_text(resp)
    return MENU


def main():
    application = ApplicationBuilder().token(os.getenv("BOT_TOKEN")).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start), CommandHandler("menu", menu)],
        states={
            LANGUAGE: [MessageHandler(filters.TEXT, set_language)],
            MENU: [
                MessageHandler(filters.Regex("درباره من و همکاری با ما|About me|حول|关于"), about_me),
                MessageHandler(filters.Regex("هوش مصنوعی|AI|ذكاء|人工智能"), chat_ai),
            ],
            COLLECT_NAME: [MessageHandler(filters.TEXT, collect_name)],
            COLLECT_JOB: [MessageHandler(filters.TEXT, collect_job)],
            COLLECT_PHONE: [MessageHandler(filters.TEXT, collect_phone)],
            COLLECT_EMAIL: [MessageHandler(filters.TEXT, collect_email)],
        },
        fallbacks=[CommandHandler("menu", menu)]
    )

    application.add_handler(conv_handler)
    app.run("0.0.0.0", port=int(os.environ.get("PORT", 5000)))


if __name__ == "__main__":
    asyncio.run(main())
