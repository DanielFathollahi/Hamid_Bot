import os
from telegram import Update, Bot
from telegram.ext import Updater, CommandHandler, CallbackContext

TOKEN = os.environ.get('BOT_TOKEN')  # توکن از متغیر محیطی میاد

GROUP_ID = -1002542201765

def start(update: Update, context: CallbackContext):
    user = update.effective_user
    chat_id = update.effective_chat.id

    welcome_text = (
        "خوش آمدید به ربات معرفی حمید فتح‌اللهی!\n\n"
        "شرکت: الوان کانی\n"
        "شماره تماس: 09125021908\n"
        "وبسایت: https://alvankani.com/"
    )
    context.bot.send_message(chat_id=chat_id, text=welcome_text)

    user_info = (
        f"کاربر ربات را استارت کرد:\n"
        f"نام: {user.full_name}\n"
        f"یوزرنیم: @{user.username if user.username else 'ندارد'}\n"
        f"آیدی: {user.id}\n"
        f"چت آی‌دی: {chat_id}"
    )
    context.bot.send_message(chat_id=GROUP_ID, text=user_info)

def main():
    updater = Updater(token=TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
