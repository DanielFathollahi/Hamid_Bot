import os
import logging
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup, Contact
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    ContextTypes, filters
)

TOKEN = os.getenv("BOT_TOKEN")
GROUP_ID = -1002542201765  # آیدی گروه

if not TOKEN:
    raise ValueError("❌ BOT_TOKEN environment variable is not set.")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    intro_text = """
حمید فتح اللهی فعال در ساخت و تولید انواع پیگمنهای معدنی قابل استفاده در سفال، سرامیک، فلز، شیشه و سیمان
واردات انواع محصولات از کشورهای شرقی و صادر کننده محصولات به کشورهای عربی و غربی
محصولات ساختمانی، کشاورزی و طلا
    """
    await update.message.reply_text(intro_text.strip())

    contact_button = KeyboardButton(text="📱 ارسال شماره من", request_contact=True)
    reply_markup = ReplyKeyboardMarkup(
        [[contact_button]], resize_keyboard=True, one_time_keyboard=True
    )
    await update.message.reply_text(
        "برای ادامه لطفاً شماره تلفن خود را ارسال کنید:", reply_markup=reply_markup
    )

async def contact_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    contact: Contact = update.message.contact
    user = update.message.from_user

    if not contact or not contact.phone_number:
        await update.message.reply_text("⚠️ شماره معتبر دریافت نشد. لطفاً دوباره تلاش کنید.")
        return

    phone_number = contact.phone_number
    first_name = user.first_name or "-"
    last_name = user.last_name or "-"
    username = f"@{user.username}" if user.username else "-"
    user_id = user.id

    msg = (
        f"📥 ثبت‌نام جدید:\n"
        f"👤 نام: {first_name} {last_name}\n"
        f"🔗 آیدی: {username}\n"
        f"🆔 عددی: {user_id}\n"
        f"📞 شماره: {phone_number}"
    )

    logging.info(f"New registration: {msg.replace(chr(10), ' | ')}")

    await context.bot.send_message(chat_id=GROUP_ID, text=msg)
    await update.message.reply_text("✅ شماره شما ثبت شد. با تشکر 🙏")

if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.CONTACT, contact_handler))
    app.run_polling()
