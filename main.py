import os
import threading
from flask import Flask
from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup
)
from telegram.ext import (
    Application, CommandHandler, MessageHandler, CallbackQueryHandler,
    ConversationHandler, ContextTypes, filters
)
from openai import OpenAI

# === تنظیمات ===
TOKEN = os.getenv("TOKEN")
GROUP_CHAT_ID = -1002542201765
AI_API_KEY = os.getenv("HF_TOKEN")  # حالا از محیط می‌گیره

app = Flask(__name__)

client = OpenAI(
    base_url="https://router.huggingface.co/v1",
    api_key=AI_API_KEY,
)

# === حالت‌ها ===
SELECT_LANGUAGE, SELECT_OPTION, ASK_DESCRIPTION, ASK_PHONE, CHAT_AI = range(5)

@app.route('/')
def ping():
    return 'pong'


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [
            InlineKeyboardButton("🇮🇷 فارسی", callback_data='fa'),
            InlineKeyboardButton("🇺🇸 English", callback_data='en')
        ],
        [
            InlineKeyboardButton("🇸🇦 عربي", callback_data='ar'),
            InlineKeyboardButton("🇨🇳 中文", callback_data='zh')
        ]
    ]
    await update.message.reply_text("🌐 لطفا زبان مورد نظر را انتخاب کنید:",
                                    reply_markup=InlineKeyboardMarkup(keyboard))
    return SELECT_LANGUAGE


async def select_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data['lang'] = query.data

    keyboard = [
        [
            InlineKeyboardButton("ℹ️ درباره من", callback_data='about_me'),
            InlineKeyboardButton("🤖 چت با هوش مصنوعی", callback_data='chat_ai')
        ]
    ]
    await query.edit_message_text("✅ گزینه‌ای را انتخاب کنید:",
                                  reply_markup=InlineKeyboardMarkup(keyboard))
    return SELECT_OPTION


async def select_option(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == 'about_me':
        return await intro(query, context)
    elif query.data == 'chat_ai':
        context.user_data['chat_count'] = 0
        await query.edit_message_text("💬 پیام خود را بفرستید (حداکثر 11 پیام):")
        return CHAT_AI


async def intro(update_or_query, context: ContextTypes.DEFAULT_TYPE):
    text = """
📌 معرفی: حمید فتح‌اللهی

سلام و خوش‌آمدید 🌟

من حمید فتح‌اللهی هستم، فعال در حوزه تولید و عرضه انواع پیگمنت‌های معدنی قابل استفاده در:
🎨 سفال، سرامیک، فلز، شیشه و سیمان

همچنین:
🌏 واردکننده محصولات از کشورهای شرقی
🚢 صادرکننده به بازارهای عربی و غربی

✨ محصولات ما شامل طیف گسترده‌ای از:
🏗️ مصالح ساختمانی
🌱 محصولات کشاورزی
💎 و مواد اولیه صنعت طلا
"""
    await update_or_query.message.reply_text(text)
    await update_or_query.message.reply_text("لطفاً درباره کار خود و خودتان توضیح دهید ✍️")
    return ASK_DESCRIPTION


async def ask_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["description"] = update.message.text
    keyboard = [[KeyboardButton("📱 ارسال شماره", request_contact=True)]]
    markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    await update.message.reply_text("لطفاً شماره تلفن خود را ارسال کنید 📱", reply_markup=markup)
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


async def chat_ai(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get('chat_count', 0) >= 11:
        await update.message.reply_text("🚫 به حداکثر تعداد چت (11) رسیدید.")
        return ConversationHandler.END

    user_input = update.message.text.lower()
    context.user_data['chat_count'] += 1

    # پاسخ‌های سفارشی
    if "توکن" in user_input:
        await update.message.reply_text("🚫 نمی‌توانم در این مورد کمکی کنم.")
        return CHAT_AI
    elif "کی ساخته" in user_input:
        await update.message.reply_text("👤 این ربات توسط دانیال فتح‌اللهی ساخته شده است.")
        return CHAT_AI
    elif "درباره" in user_input and "کار" in user_input:
        await update.message.reply_text("✨ ما جزو بهترین‌ها هستیم و پیشنهاد ما خودمان است.")
        return CHAT_AI

    # درخواست به هوش مصنوعی
    completion = client.chat.completions.create(
        model="moonshotai/Kimi-K2-Instruct",
        messages=[
            {"role": "user", "content": update.message.text}
        ]
    )

    reply = completion.choices[0].message.content.strip()
    await update.message.reply_text(reply)

    return CHAT_AI


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("لغو شد.")
    return ConversationHandler.END


def run_bot():
    app_tg = Application.builder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            SELECT_LANGUAGE: [CallbackQueryHandler(select_language)],
            SELECT_OPTION: [CallbackQueryHandler(select_option)],
            ASK_DESCRIPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_phone)],
            ASK_PHONE: [
                MessageHandler(filters.CONTACT, collect),
                MessageHandler(filters.TEXT & ~filters.COMMAND, collect)
            ],
            CHAT_AI: [MessageHandler(filters.TEXT & ~filters.COMMAND, chat_ai)]
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )

    app_tg.add_handler(conv_handler)
    app_tg.run_polling()


if __name__ == "__main__":
    threading.Thread(target=lambda: app.run(host="0.0.0.0", port=8000)).start()
    run_bot()
