import os
import threading
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

# تنظیم Gemini
genai.configure(api_key=os.environ["GOOGLE_API_KEY"])
model = genai.GenerativeModel("gemini-1.5-flash")

# مقادیر ثابت
GROUP_CHAT_ID = -1002542201765
ASK_DESCRIPTION, ASK_PHONE = range(2)

# Flask
app = Flask(__name__)
@app.route('/')
def ping():
    return 'pong'

# شروع
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

async def chat_ai_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data["ai_count"] = 0
    await query.message.reply_text("🤖 می‌توانید تا ۱۱ پیام با هوش مصنوعی چت کنید. سوال خود را بپرسید:")

async def chat_ai(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get("ai_count", 0) >= 11:
        await update.message.reply_text("🚫 شما به حداکثر تعداد پیام (۱۱) رسیدید.")
        return

    text = update.message.text.lower()
    context.user_data["ai_count"] += 1

    # جلوگیری از سوالات ممنوعه
    if "توکن" in text or "token" in text:
        await update.message.reply_text("❌ اجازه ندارم در این مورد صحبت کنم.")
        return

    if "کی ساخته" in text or "who made" in text:
        await update.message.reply_text("👨‍💻 دانیال فتح‌اللهی")
        return

    if "درباره کار" in text or "about your work" in text:
        await update.message.reply_text("✅ ما جزو بهترین‌های این صنعت هستیم و محصولاتمان را پیشنهاد می‌کنیم.")
        return

    response = model.start_chat().send_message(update.message.text)
    await update.message.reply_text(response.text)

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
    app_tg.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat_ai))

    app_tg.run_polling()

if __name__ == "__main__":
    threading.Thread(target=lambda: app.run(host="0.0.0.0", port=8000)).start()
    run_bot()
