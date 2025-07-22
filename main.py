import os
import threading
from flask import Flask
from datetime import datetime
from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup
)
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, ContextTypes, ConversationHandler, filters
)
from openai import OpenAI

TOKEN = os.getenv("BOT_TOKEN")
HF_TOKEN = os.getenv("HF_TOKEN")
GROUP_CHAT_ID = -1002542201765

app = Flask(__name__)
client = OpenAI(api_key=HF_TOKEN)

LANGUAGE, MENU, CHAT_AI = range(3)
user_sessions = {}

TEXTS = {
    "choose_lang": "🌐 لطفا زبان خود را انتخاب کنید:",
    "languages": [
        ("فارسی 🇮🇷", "fa"),
        ("English 🇺🇸", "en"),
        ("العربية 🇸🇦", "ar"),
        ("中文 🇨🇳", "zh"),
    ],
    "menu": {
        "fa": "✅ لطفا یکی از گزینه‌ها را انتخاب کنید:",
        "en": "✅ Please choose an option:",
        "ar": "✅ الرجاء اختيار خيار:",
        "zh": "✅ 请选择一个选项：",
    },
    "options": {
        "about": {
            "fa": "📋 درباره ما و همکاری",
            "en": "📋 About Us & Cooperation",
            "ar": "📋 معلومات عنا والتعاون",
            "zh": "📋 关于我们和合作",
        },
        "chat": {
            "fa": "🤖 چت با هوش مصنوعی",
            "en": "🤖 Chat with AI",
            "ar": "🤖 الدردشة مع الذكاء الاصطناعي",
            "zh": "🤖 与人工智能聊天",
        },
        "back": {
            "fa": "🔙 بازگشت به منو",
            "en": "🔙 Back to Menu",
            "ar": "🔙 العودة إلى القائمة",
            "zh": "🔙 返回菜单",
        }
    },
    "intro_about": {
        "fa": "📌 معرفی: حمید فتح‌اللهی\n\nسلام و خوش‌آمدید 🌟\n\nمن حمید فتح‌اللهی هستم، فعال در حوزه تولید و عرضه انواع پیگمنت‌های معدنی قابل استفاده در:\n🎨 سفال، سرامیک، فلز، شیشه و سیمان\n\nهمچنین:\n🌏 واردکننده محصولات از کشورهای شرقی\n🚢 صادرکننده به بازارهای عربی و غربی\n\n✨ محصولات ما شامل:\n🏗️ مصالح ساختمانی\n🌱 محصولات کشاورزی\n💎 مواد اولیه صنعت طلا\n🖨️ جوهرهای چاپ دیجیتال",
        "en": "📌 Introduction: Hamid Fathollahi\n\nWelcome! 🌟\n\nI'm Hamid Fathollahi, specialized in the production and supply of various mineral pigments used in:\n🎨 Pottery, ceramics, metal, glass, and cement.\n\nAdditionally:\n🌏 Importer of products from Eastern countries\n🚢 Exporter to Arab and Western markets\n\n✨ Our products include:\n🏗️ Construction materials\n🌱 Agricultural goods\n💎 Raw materials for the gold industry\n🖨️ Digital printing inks",
        "ar": "📌 التعريف: حميد فتح اللهي\n\nمرحبًا بكم 🌟\n\nأنا حميد فتح اللهي، متخصص في إنتاج وتوريد أنواع مختلفة من الأصباغ المعدنية المستخدمة في:\n🎨 الفخار، السيراميك، المعادن، الزجاج والإسمنت.\n\nكذلك:\n🌏 مستورد للمنتجات من الدول الشرقية\n🚢 ومصدر للأسواق العربية والغربية\n\n✨ منتجاتنا تشمل:\n🏗️ مواد البناء\n🌱 المنتجات الزراعية\n💎 المواد الأولية لصناعة الذهب\n🖨️ أحبار الطباعة الرقمية",
        "zh": "📌 介绍：哈米德·法索拉希\n\n欢迎光临 🌟\n\n我是哈米德·法索拉希，专注于生产和供应各种用于以下领域的矿物颜料：\n🎨 陶瓷、金属、玻璃、水泥和陶器\n\n此外：\n🌏 从东方国家进口产品\n🚢 向阿拉伯和西方市场出口\n\n✨ 我们的产品包括：\n🏗️ 建筑材料\n🌱 农产品\n💎 黄金行业的原材料\n🖨️ 数字打印墨水"
    }
}


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton(text, callback_data=lang)] for text, lang in TEXTS["languages"]]
    await update.message.reply_text(TEXTS["choose_lang"], reply_markup=InlineKeyboardMarkup(keyboard))
    return LANGUAGE


async def set_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = update.callback_query.data
    context.user_data["lang"] = lang
    user_sessions[update.effective_user.id] = {"count": 0, "date": datetime.now().date()}
    return await show_menu(update, context)


async def show_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data["lang"]
    keyboard = [
        [InlineKeyboardButton(TEXTS["options"]["about"][lang], callback_data="about")],
        [InlineKeyboardButton(TEXTS["options"]["chat"][lang], callback_data="chat")]
    ]
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(TEXTS["menu"][lang], reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        await update.message.reply_text(TEXTS["menu"][lang], reply_markup=InlineKeyboardMarkup(keyboard))
    return MENU


async def handle_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    lang = context.user_data["lang"]
    if query.data == "about":
        await query.answer()
        await query.edit_message_text(TEXTS["intro_about"][lang],
                                      reply_markup=InlineKeyboardMarkup([
                                          [InlineKeyboardButton(TEXTS["options"]["back"][lang], callback_data="back")]
                                      ]))
        return MENU
    elif query.data == "chat":
        await query.answer()
        await query.edit_message_text(TEXTS["options"]["chat"][lang],
                                      reply_markup=InlineKeyboardMarkup([
                                          [InlineKeyboardButton(TEXTS["options"]["back"][lang], callback_data="back")]
                                      ]))
        return CHAT_AI
    elif query.data == "back":
        return await show_menu(update, context)


async def chat_ai(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    session = user_sessions.get(user_id, {"count": 0, "date": datetime.now().date()})
    if session["date"] != datetime.now().date():
        session = {"count": 0, "date": datetime.now().date()}
    if session["count"] >= 5:
        await update.message.reply_text("❌ شما به حداکثر تعداد چت روزانه رسیدید.")
        return CHAT_AI

    session["count"] += 1
    user_sessions[user_id] = session

    msg = update.message.text.lower()
    lang = context.user_data["lang"]

    # اگر پرسید "حمید فتح اللهی"
    if "حمید فتح اللهی" in msg or "hamid fathollahi" in msg or "حميد فتح اللهي" in msg:
        await update.message.reply_text(TEXTS["intro_about"][lang])
        return CHAT_AI

    completion = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "Answer briefly and only once. If asked about Hamid Fathollahi, send company info."},
            {"role": "user", "content": msg}
        ]
    )
    reply = completion.choices[0].message.content
    await update.message.reply_text(reply)
    return CHAT_AI


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ لغو شد.")
    return ConversationHandler.END


def run_bot():
    app_tg = Application.builder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            LANGUAGE: [CallbackQueryHandler(set_language)],
            MENU: [CallbackQueryHandler(handle_menu)],
            CHAT_AI: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, chat_ai),
                CallbackQueryHandler(handle_menu)
            ]
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )
    app_tg.add_handler(conv_handler)
    app_tg.run_polling()


if __name__ == "__main__":
    threading.Thread(target=lambda: app.run(host="0.0.0.0", port=8000)).start()
    run_bot()
