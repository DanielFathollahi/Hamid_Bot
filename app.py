import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# توکن رو از Environment Variable می‌گیره
TOKEN = os.environ.get('BOT_TOKEN')

# آی‌دی گروهی که پیام باید به اون ارسال بشه
GROUP_ID = -1002542201765

# تابع برای هندل کردن دستور /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    chat_id = update.effective_chat.id

    # پیام خوش آمدگویی برای کاربر
    welcome_text = (
        "خوش آمدید به ربات معرفی حمید فتح‌اللهی!\n\n"
        "📌 شرکت: الوان کانی\n"
        "📞 شماره تماس: 09125021908\n"
        "🌐 وبسایت: https://alvankani.com/"
    )
    await context.bot.send_message(chat_id=chat_id, text=welcome_text)

    # اطلاعات کاربر برای ارسال به گروه
    user_info = (
        f"📥 کاربر جدید ربات را استارت کرد:\n"
        f"👤 نام: {user.full_name}\n"
        f"🔗 یوزرنیم: @{user.username if user.username else 'ندارد'}\n"
        f"🆔 آیدی: {user.id}\n"
        f"💬 چت آی‌دی: {chat_id}"
    )
    await context.bot.send_message(chat_id=GROUP_ID, text=user_info)

# تابع main
async def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    await app.run_polling()

if __name__ == '__main__':
    import asyncio
    asyncio.run(main())
