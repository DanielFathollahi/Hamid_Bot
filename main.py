import os
import logging
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup, Contact
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    ContextTypes, filters
)
from flask import Flask, request

TOKEN = os.getenv("BOT_TOKEN")
GROUP_ID = -1002542201765

if not TOKEN:
    raise ValueError("❌ BOT_TOKEN environment variable is not set.")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

app_flask = Flask(__name__)
application = None


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    intro_text = """
📌 **معرفی: حمید فتح‌اللهی**

سلام و خوش‌آمدید 🌟

من **حمید فتح‌اللهی** هستم، فعال در حوزه تولید و عرضه انواع **پیگمنت‌های معدنی** قابل استفاده در:
🎨 سفال، سرامیک، فلز، شیشه و سیمان

🌏 واردکننده محصولات از کشورهای شرقی  
🚢 صادرکننده به بازارهای عربی و غربی

✨ محصولات ما شامل:
🏗️ مصالح ساختمانی
🌱 محصولات کشاورزی
💎 و مواد اولیه صنعت طلا

لطفاً برای ادامه، شماره تلفن خود را ارسال کنید. 📱
    """
    await update.message.reply_markdown(intro_text.strip())

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


@app_flask.route("/webhook", methods=["POST"])
def webhook():
    if request.method == "POST":
        json_update = request.get_json(force=True)
        update = Update.de_json(json_update, application.bot)
        application.update_queue.put(update)
        return "ok"
    return "error", 403


if __name__ == "__main__":
    application = ApplicationBuilder().token(TOKEN).concurrent_updates(True).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.CONTACT, contact_handler))

    import asyncio
    async def set_webhook():
        # Render domain مثلا https://your-app.onrender.com
        render_url = os.getenv("RENDER_EXTERNAL_URL") or "https://your-app.onrender.com"
        webhook_url = render_url + "/webhook"
        await application.bot.set_webhook(webhook_url)
        logging.info("✅ Webhook set to: %s", webhook_url)

    asyncio.run(set_webhook())
    app_flask.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
