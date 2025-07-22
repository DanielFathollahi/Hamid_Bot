import os
import threading
from flask import Flask
from telegram import (
    Update, KeyboardButton, ReplyKeyboardMarkup,
    InlineKeyboardButton, InlineKeyboardMarkup
)
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler, MessageHandler,
    ConversationHandler, ContextTypes, filters
)
from openai import OpenAI

# 🪪 TOKEN ها
TOKEN = os.getenv("TOKEN")
HF_TOKEN = os.getenv("HF_TOKEN")
GROUP_CHAT_ID = -1002542201765

# 🌐 Flask
app = Flask(__name__)
@app.route('/')
def ping():
    return 'pong'

# 📍 وضعیت‌ها
ASK_LANGUAGE, CHOOSE_ACTION, ASK_DESCRIPTION, ASK_PHONE, AI_CHAT = range(5)

# 🧠 هوش مصنوعی
client = OpenAI(
    base_url="https://router.huggingface.co/v1",
    api_key=HF_TOKEN,
)

# 🌍 ترجمه‌ها
translations = {
    'fa': {
        'intro': "🌐 لطفاً یکی از گزینه‌های زیر را انتخاب کنید:",
        'about': "📄 درباره‌ی من",
        'chat': "🤖 چت با هوش مصنوعی ما",
        'desc': "لطفاً درباره کار خود و خودتان توضیح دهید ✍️",
        'phone': "لطفاً شماره تلفن خود را ارسال کنید 📱",
        'thanks': "✅ اطلاعات شما ثبت شد. ممنون 🙏",
        'cancel': "لغو شد.",
        'chat_start': "🤖 می‌توانید با هوش مصنوعی ما چت کنید (حداکثر ۱۱ پیام). پیام خود را ارسال کنید:"
    },
    'en': {
        'intro': "🌐 Please choose one of the options below:",
        'about': "📄 About Me",
        'chat': "🤖 Chat with Our AI",
        'desc': "Please describe yourself and your work ✍️",
        'phone': "Please send your phone number 📱",
        'thanks': "✅ Your information has been recorded. Thank you 🙏",
        'cancel': "Cancelled.",
        'chat_start': "🤖 You can chat with our AI (up to 11 messages). Please send your message:"
    },
    'ar': {
        'intro': "🌐 يرجى اختيار أحد الخيارات التالية:",
        'about': "📄 عني",
        'chat': "🤖 الدردشة مع ذكائنا الاصطناعي",
        'desc': "يرجى تقديم نفسك وعملك ✍️",
        'phone': "يرجى إرسال رقم هاتفك 📱",
        'thanks': "✅ تم تسجيل معلوماتك. شكرًا 🙏",
        'cancel': "تم الإلغاء.",
        'chat_start': "🤖 يمكنك الدردشة مع ذكائنا الاصطناعي (حتى ١١ رسالة). أرسل رسالتك:"
    },
    'zh': {
        'intro': "🌐 请选择以下选项之一：",
        'about': "📄 关于我",
        'chat': "🤖 与我们的AI聊天",
        'desc': "请介绍一下您自己和您的工作 ✍️",
        'phone': "请发送您的电话号码 📱",
        'thanks': "✅ 您的信息已记录。谢谢 🙏",
        'cancel': "已取消。",
        'chat_start': "🤖 您可以与我们的AI聊天（最多11条消息）。请发送您的消息："
    }
}

# 🚀 start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🇮🇷 فارسی", callback_data='fa')],
        [InlineKeyboardButton("🇬🇧 English", callback_data='en')],
        [InlineKeyboardButton("🇸🇦 العربية", callback_data='ar')],
        [InlineKeyboardButton("🇨🇳 中文", callback_data='zh')]
    ]
    markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("لطفاً زبان خود را انتخاب کنید 🌐", reply_markup=markup)
    return ASK_LANGUAGE

# 🌍 زبان انتخاب شد
async def choose_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    lang = query.data
    context.user_data['lang'] = lang

    keyboard = [
        [
            InlineKeyboardButton(translations[lang]['about'], callback_data='about'),
            InlineKeyboardButton(translations[lang]['chat'], callback_data='chat')
        ]
    ]
    markup = InlineKeyboardMarkup(keyboard)
    await query.message.reply_text(translations[lang]['intro'], reply_markup=markup)
    return CHOOSE_ACTION

# 👆 انتخاب گزینه (درباره یا چت)
async def choose_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    choice = query.data
    lang = context.user_data.get('lang', 'fa')

    if choice == 'about':
        await query.message.reply_text(translations[lang]['desc'])
        return ASK_DESCRIPTION
    elif choice == 'chat':
        context.user_data['ai_messages'] = []
        context.user_data['ai_count'] = 0
        await query.message.reply_text(translations[lang]['chat_start'])
        return AI_CHAT

# 📄 درباره من
async def ask_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data.get('lang', 'fa')
    context.user_data["description"] = update.message.text

    keyboard = [[KeyboardButton("📱 ارسال شماره", request_contact=True)]]
    markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)

    await update.message.reply_text(translations[lang]['phone'], reply_markup=markup)
    return ASK_PHONE

async def collect(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data.get('lang', 'fa')
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
    await update.message.reply_text(translations[lang]['thanks'])
    return ConversationHandler.END

# 🤖 چت با هوش مصنوعی
async def ai_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data.get('lang', 'fa')
    user_input = update.message.text
    messages = context.user_data.get('ai_messages', [])
    count = context.user_data.get('ai_count', 0)

    if count >= 11:
        await update.message.reply_text("🚫 شما به حداکثر ۱۱ پیام رسیدید.")
        return ConversationHandler.END

    # قوانین
    lowered = user_input.lower()
    if "token" in lowered or "توکن" in lowered:
        await update.message.reply_text("🚫 اطلاعات حساس قابل ارائه نیست.")
        return AI_CHAT
    if "سازنده" in lowered or "who built" in lowered:
        await update.message.reply_text("👤 دانیال فتح‌اللهی")
        return AI_CHAT
    if "کار" in lowered or "job" in lowered:
        await update.message.reply_text("✅ ما جزو بهترین‌ها هستیم و ما را پیشنهاد می‌کنم.")
        return AI_CHAT

    # چت
    messages.append({"role": "user", "content": user_input})

    completion = client.chat.completions.create(
        model="moonshotai/Kimi-K2-Instruct",
        messages=messages
    )
    ai_reply = completion.choices[0].message.content
    await update.message.reply_text(ai_reply)

    messages.append({"role": "assistant", "content": ai_reply})
    context.user_data['ai_messages'] = messages
    context.user_data['ai_count'] = count + 1

    return AI_CHAT

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data.get('lang', 'fa')
    await update.message.reply_text(translations[lang]['cancel'])
    return ConversationHandler.END

def run_bot():
    app_tg = Application.builder().token(TOKEN).build()
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            ASK_LANGUAGE: [CallbackQueryHandler(choose_language)],
            CHOOSE_ACTION: [CallbackQueryHandler(choose_action)],
            ASK_DESCRIPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_phone)],
            ASK_PHONE: [
                MessageHandler(filters.CONTACT, collect),
                MessageHandler(filters.TEXT & ~filters.COMMAND, collect)
            ],
            AI_CHAT: [MessageHandler(filters.TEXT & ~filters.COMMAND, ai_chat)]
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )
    app_tg.add_handler(conv_handler)
    app_tg.run_polling()

if __name__ == "__main__":
    threading.Thread(target=lambda: app.run(host="0.0.0.0", port=8000)).start()
    run_bot()
