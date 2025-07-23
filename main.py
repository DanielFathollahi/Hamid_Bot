import os
from flask import Flask
from telegram import Update
from telegram.ext import (
    Application, CommandHandler, MessageHandler, filters, ContextTypes
)
from huggingface_hub import InferenceClient

# گرفتن توکن‌ها از محیط سیستم (Render Environment Variables)
BOT_TOKEN = os.environ["BOT_TOKEN"]
HF_TOKEN = os.environ["HF_TOKEN"]

# تنظیم کلاینت Mistral
mistral = InferenceClient(
    model="mistralai/Mistral-7B-Instruct-v0.2",
    token=HF_TOKEN
)

# تابع برای گرفتن پاسخ از Mistral
async def ask_mistral(prompt: str) -> str:
    full_prompt = f"[INST] {prompt.strip()} [/INST]"
    response = mistral.text_generation(
        prompt=full_prompt,
        max_new_tokens=512,
        temperature=0.7,
        do_sample=True
    )
    return response.strip()

# هندلر پیام‌ها
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_input = update.message.text
    await update.message.chat.send_action(action="typing")
    try:
        response = await ask_mistral(user_input)
        await update.message.reply_text(response)
    except Exception as e:
        await update.message.reply_text("❌ خطایی رخ داد.")
        print(f"Error: {e}")

# دستور /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("سلام! سوالتو بپرس.")

# دستور /help
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("راهنما: فقط سوالت رو بفرست.")

# اپلیکیشن تلگرام
def telegram_app():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    return app

# سرور Flask برای Render
flask_app = Flask(__name__)

@flask_app.route("/")
def index():
    return "🤖 Bot is running."

# اجرای اپلیکیشن
def main():
    tg_app = telegram_app()
    tg_app.run_polling()

if __name__ == "__main__":
    import threading
    threading.Thread(target=main).start()
    flask_app.run(host="0.0.0.0", port=8000)
