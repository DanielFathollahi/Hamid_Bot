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

# متغیرهای محیطی از Render
TOKEN = os.getenv("BOT_TOKEN")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GROUP_CHAT_ID = -1002542201765  # گروه مقصد

# اپلیکیشن Flask برای UptimeRobot
app = Flask(__name__)

# مراحل گفتگو
LANGUAGE, MENU, AI_CHAT, COLLECT_INFO = range(4)

# زبان‌ها
languages = {
    "fa": {"flag": "🇮🇷", "name": "فارسی"},
    "en": {"flag": "🇬🇧", "name": "English"},
    "ar": {"flag": "🇸🇦", "name": "العربية"},
    "zh": {"flag": "🇨🇳", "name": "中文"}
}

# متن درباره ما
about_us = {
    "fa": """📌 درباره من و همکاری با ما:

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
    "en": """📌 About me & Cooperation:

Hello & welcome 🌟

I am Hamid Fathollahi, active in the production and supply of mineral pigments for:
🎨 Pottery, ceramics, metals, glass & cement

Also:
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

كما أنني:
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

同时：
🌏 从东方国家进口
🚢 向阿拉伯和西方市场出口

✨ 我们的产品包括：
🏗️ 建筑材料
🌱 农产品
💎 黄金行业原材料
🖨️ 数码印刷油墨
"""
}

user_sessions = {}

@app.route('/')
def ping():
    return 'pong'

# وقتی استارت زده میشه: خوش‌آمد + منو
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = "fa"  # پیش‌فرض فارسی
    context.user_data["lang"] = lang
    user_sessions[update.effective_user.id] = {"count": 0, "date": datetime.now().date()}

    await update.message.reply_text(about_us[lang])

    return await show_menu(update, context)

# نمایش منو
async def show_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data.get("lang", "fa")
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
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(buttons))
    return MENU

# دکمه درباره ما کلیک شد
async def about(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data.get("lang", "fa")
    await update.callback_query.answer()
    await update.callback_query.message.reply_text(about_us[lang])

    # درخواست اطلاعات کاربر
    prompt = {
        "fa": "✍️ لطفاً نام و نام خانوادگی، شغل و شماره تماس خود را برای همکاری ارسال کنید:",
        "en": "✍️ Please send your full name, profession, and phone number for cooperation:",
        "ar": "✍️ يرجى إرسال اسمك الكامل، مهنتك ورقم هاتفك للتعاون:",
        "zh": "✍️ 请发送您的姓名、职业和联系电话以便合作："
    }[lang]

    await update.callback_query.message.reply_text(prompt)
    return COLLECT_INFO

# کاربر اطلاعات همکاری را می‌فرسته
async def collect_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    info = update.message.text
    user = update.effective_user

    msg = f"👤 اطلاعات همکاری جدید:\n\n" \
          f"نام کاربر: {user.full_name}\n" \
          f"یوزرنیم: @{user.username or '---'}\n" \
          f"متن ارسالی:\n{info}"

    # ارسال به گروه
    await context.bot.send_message(chat_id=GROUP_CHAT_ID, text=msg)

    await update.message.reply_text("✅ اطلاعات شما با موفقیت ثبت و ارسال شد. ممنون از شما!")
    return MENU

# شروع چت با هوش مصنوعی
async def ai_chat_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    await update.callback_query.message.reply_text("✍️ پیام خود را برای هوش مصنوعی بفرستید. برای بازگشت /menu را بزنید.")
    return AI_CHAT

# پاسخ AI به پیام کاربر
async def ai_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    lang = context.user_data.get("lang", "fa")
    today = datetime.now().date()
    session = user_sessions.get(user_id)

    if not session:
        session = {"count": 0, "date": today}
        user_sessions[user_id] = session

    if session["date"] != today:
        session["count"] = 0
        session["date"] = today

    if session["count"] >= 5:
        await update.message.reply_text({
            "fa": "🚫 شما امروز به ۵ پیام رسیدید.",
            "en": "🚫 You reached the 5 messages limit today.",
            "ar": "🚫 لقد وصلت إلى 5 رسائل اليوم.",
            "zh": "🚫 您今天已达到5条消息的限制。"
        }[lang])
        return AI_CHAT

    try:
        model = GenerativeModel("gemini-pro", api_key=GOOGLE_API_KEY)
        response = model.generate_content([update.message.text])
        answer = response.text.strip().split("\n")[0]
        session["count"] += 1
        await update.message.reply_text(answer)
    except Exception as e:
        print("AI Error:", e)
        await update.message.reply_text({
            "fa": "❌ خطا در پاسخ AI",
            "en": "❌ AI error",
            "ar": "❌ خطأ في الذكاء الاصطناعي",
            "zh": "❌ AI 出错"
        }[lang])

    return AI_CHAT

# بازگشت به منو
async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    return await show_menu(update, context)

# لغو گفتگو
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ گفتگو لغو شد.")
    return ConversationHandler.END

# راه‌اندازی برنامه
def main():
    app_tg = Application.builder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            MENU: [
                CallbackQueryHandler(about, pattern="^about$"),
                CallbackQueryHandler(ai_chat_start, pattern="^ai_chat$")
            ],
            AI_CHAT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, ai_chat),
                CommandHandler("menu", menu)
            ],
            COLLECT_INFO: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, collect_info)
            ]
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )

    app_tg.add_handler(conv_handler)
    app_tg.run_polling()

if __name__ == "__main__":
    import threading
    threading.Thread(target=lambda: app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))).start()
    main()
