import os
import threading
from datetime import datetime, date
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

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("فارسی", callback_data="lang_fa")],
        [InlineKeyboardButton("English", callback_data="lang_en")],
        [InlineKeyboardButton("العربية", callback_data="lang_ar")],
        [InlineKeyboardButton("中文", callback_data="lang_zh")]
    ]
    await update.message.reply_text(
        "🌐 لطفاً زبان خود را انتخاب کنید:", 
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def language_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    lang = query.data.split("_")[1]
    context.user_data["lang"] = lang

    keyboard = [
        [InlineKeyboardButton("📄 درباره‌ی ما", callback_data="about_us")],
        [InlineKeyboardButton("🤖 چت با هوش مصنوعی", callback_data="chat_ai")]
    ]
    await query.message.reply_text(
        "👇 یکی از گزینه‌های زیر را انتخاب کنید:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def about_us(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    intro_text = """
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
"""
    await query.message.reply_text(intro_text)
    await query.message.reply_text("✍️ لطفاً درباره‌ی کار خود و خودتان توضیح دهید:")
    return ASK_DESCRIPTION

async def ask_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["description"] = update.message.text
    keyboard = [[KeyboardButton("📱 ارسال شماره", request_contact=True)]]
    markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    await update.message.reply_text("📞 لطفاً شماره تلفن خود را ارسال کنید:", reply_markup=markup)
    return ASK_PHONE

async def collect(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
    await update.message.reply_text("✅ اطلاعات شما ثبت شد. ممنون 🙏")
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

    await query.message.reply_text(
        "🤖 می‌توانید تا ۵ پیام در روز با هوش مصنوعی چت کنید. سوال خود را بپرسید:"
    )

async def chat_ai(update: Update, context: ContextTypes.DEFAULT_TYPE):
    reset_ai_counter_if_new_day(context)
    count = context.user_data.get("ai_count", 0)

    if count >= 5:
        await update.message.reply_text("🚫 شما به حداکثر تعداد پیام‌های مجاز امروز (۵ پیام) رسیدید.")
        return

    text = update.message.text.lower()

    # افزایش شمارنده
    context.user_data["ai_count"] = count + 1

    # جلوگیری از سوالات ممنوعه
    if "توکن" in text or "token" in text:
        await update.message.reply_text("❌ اجازه ندارم در این مورد صحبت کنم.")
        return

    # پاسخ به سوال درباره حمید فتح اللهی
    if "حمید فتح اللهی کیه" in text or "who is hamid fathollahi" in text:
        intro_text = """
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
"""
        await update.message.reply_text(intro_text)
        return

    # پاسخ به سوال درباره رنگ و کار ما
    if ("رنگ" in text or "پیگمنت" in text or "کار ما" in text) and ("چی" in text or "چیست" in text or "درباره" in text):
        await update.message.reply_text("✅ ما جزو بهترین‌های این صنعت هستیم و محصولاتمان را پیشنهاد می‌کنیم.")
        return

    # پاسخ هوش مصنوعی
    response = model.start_chat().send_message(update.message.text)
    await update.message.reply_text(response.text)

    # دکمه بازگشت به منوی اصلی
    keyboard = [
        [InlineKeyboardButton("🏠 بازگشت به منوی اصلی", callback_data="back_to_main")]
    ]
    await update.message.reply_text(
        "برای بازگشت به منوی اصلی اینجا کلیک کنید:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

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
