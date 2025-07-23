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

TOKEN = os.getenv("BOT_TOKEN")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GROUP_CHAT_ID = -1002542201765

app = Flask(__name__)

LANGUAGE, MENU, AI_CHAT, ASK_NAME, ASK_PHONE, ASK_EMAIL, ASK_JOB = range(7)

languages = {
    "fa": {"flag": "🇮🇷", "name": "فارسی"},
    "en": {"flag": "🇬🇧", "name": "English"},
    "ar": {"flag": "🇸🇦", "name": "العربية"},
    "zh": {"flag": "🇨🇳", "name": "中文"}
}

about_us = {
    "fa": "... (متن فارسی درباره ما) ...",
    "en": "... (English about us text) ...",
    "ar": "... (النص العربي عني) ...",
    "zh": "... (中文关于我文本) ..."
}

user_sessions = {}

@app.route('/')
def ping():
    return 'pong'

# گام 1: شروع و انتخاب زبان
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    buttons = [
        [InlineKeyboardButton(f"{v['flag']} {v['name']}", callback_data=f"lang_{k}")]
        for k, v in languages.items()
    ]
    await update.message.reply_text("🌐 لطفاً زبان خود را انتخاب کنید:\nPlease select your language:", reply_markup=InlineKeyboardMarkup(buttons))
    return LANGUAGE

# گام 2: تنظیم زبان
async def set_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = update.callback_query.data.split("_")[1]
    context.user_data["lang"] = lang
    user_sessions[update.effective_user.id] = {"count": 0, "date": datetime.now().date()}
    await update.callback_query.answer()
    return await show_menu(update, context)

# گام 3: نمایش منو اصلی
async def show_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data.get("lang", "fa")
    messages = {
        "fa": "📋 لطفاً یکی را انتخاب کنید:",
        "en": "📋 Please choose an option:",
        "ar": "📋 الرجاء اختيار خيار:",
        "zh": "📋 请选择一个选项："
    }
    buttons = [
        [InlineKeyboardButton({"fa": "📄 درباره من و همکاری", "en": "📄 About & Cooperation", "ar": "📄 عني والتعاون", "zh": "📄 关于我 & 合作"}[lang], callback_data="about")],
        [InlineKeyboardButton({"fa": "🤖 چت با هوش مصنوعی", "en": "🤖 Chat with AI", "ar": "🤖 الدردشة مع الذكاء", "zh": "🤖 与AI聊天"}[lang], callback_data="ai_chat")]
    ]
    if update.callback_query:
        await update.callback_query.message.reply_text(messages[lang], reply_markup=InlineKeyboardMarkup(buttons))
    else:
        await update.message.reply_text(messages[lang], reply_markup=InlineKeyboardMarkup(buttons))
    return MENU

# گام 4: درباره ما و ورود به مرحله گرفتن اطلاعات
async def about(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data.get("lang", "fa")
    await update.callback_query.answer()
    await update.callback_query.message.reply_text(about_us[lang])

    prompts = {
        "fa": "✍️ لطفاً نام و نام خانوادگی خود را وارد کنید:",
        "en": "✍️ Please enter your full name:",
        "ar": "✍️ الرجاء إدخال اسمك الكامل:",
        "zh": "✍️ 请输入您的全名："
    }
    await update.callback_query.message.reply_text(prompts[lang])
    return ASK_NAME

async def ask_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["full_name"] = update.message.text
    lang = context.user_data.get("lang", "fa")
    prompts = {
        "fa": "📱 شماره تماس شما؟",
        "en": "📱 Your phone number?",
        "ar": "📱 رقم هاتفك؟",
        "zh": "📱 您的电话号码？"
    }
    await update.message.reply_text(prompts[lang])
    return ASK_PHONE

async def ask_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["phone"] = update.message.text
    lang = context.user_data.get("lang", "fa")
    prompts = {
        "fa": "📧 ایمیل شما؟",
        "en": "📧 Your email?",
        "ar": "📧 بريدك الإلكتروني؟",
        "zh": "📧 您的电子邮箱？"
    }
    await update.message.reply_text(prompts[lang])
    return ASK_EMAIL

async def ask_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["email"] = update.message.text
    lang = context.user_data.get("lang", "fa")
    prompts = {
        "fa": "💼 شغل و حوزه فعالیت شما؟",
        "en": "💼 Your profession and field of activity?",
        "ar": "💼 مهنتك ومجال عملك؟",
        "zh": "💼 您的职业和业务领域？"
    }
    await update.message.reply_text(prompts[lang])
    return ASK_JOB

async def ask_job(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["job"] = update.message.text
    lang = context.user_data.get("lang", "fa")
    user = update.effective_user

    text = f"📥 اطلاعات همکاری جدید:\n\n" \
           f"👤 نام: {context.user_data['full_name']}\n" \
           f"📱 تماس: {context.user_data['phone']}\n" \
           f"📧 ایمیل: {context.user_data['email']}\n" \
           f"💼 شغل: {context.user_data['job']}\n" \
           f"🔗 یوزرنیم: @{user.username or '---'}\n" \
           f"🆔 آیدی عددی: {user.id}"

    await update.message.reply_text({
        "fa": "✅ اطلاعات شما ثبت شد. سپاس از همکاری شما.",
        "en": "✅ Your information has been submitted. Thank you!",
        "ar": "✅ تم إرسال معلوماتك. شكرًا لك!",
        "zh": "✅ 您的信息已提交，谢谢！"
    }[lang])

    await context.bot.send_message(chat_id=GROUP_CHAT_ID, text=text)
    return MENU

# چت با هوش مصنوعی
async def ai_chat_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    lang = context.user_data.get("lang", "fa")
    messages = {
        "fa": "✍️ پیام خود را برای هوش مصنوعی بفرستید. برای بازگشت /menu را بزنید.",
        "en": "✍️ Send your message to AI. Type /menu to return.",
        "ar": "✍️ أرسل رسالتك إلى الذكاء الاصطناعي. اكتب /menu للعودة.",
        "zh": "✍️ 给AI发送消息。输入 /menu 返回。"
    }
    await update.callback_query.message.reply_text(messages[lang])
    return AI_CHAT

async def ai_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    lang = context.user_data.get("lang", "fa")
    today = datetime.now().date()
    session = user_sessions.get(user_id, {"count": 0, "date": today})

    if session["date"] != today:
        session["count"] = 0
        session["date"] = today

    if session["count"] >= 5:
        await update.message.reply_text({
            "fa": "🚫 شما امروز به ۵ پیام رسیدید.",
            "en": "🚫 You reached today's 5-message limit.",
            "ar": "🚫 لقد وصلت إلى حد 5 رسائل اليوم.",
            "zh": "🚫 您今天已达到5条消息限制。"
        }[lang])
        return AI_CHAT

    try:
        model = GenerativeModel("gemini-pro", api_key=GOOGLE_API_KEY)
        response = model.generate_content([update.message.text])
        answer = response.text.strip()
        await update.message.reply_text(answer)
        session["count"] += 1
    except Exception as e:
        print("AI error:", e)
        await update.message.reply_text({
            "fa": "❌ خطا در پاسخ AI",
            "en": "❌ AI response error",
            "ar": "❌ خطأ في رد الذكاء الاصطناعي",
            "zh": "❌ AI 响应错误"
        }[lang])

    user_sessions[user_id] = session
    return AI_CHAT

async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    return await show_menu(update, context)

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ لغو شد.")
    return ConversationHandler.END

def main():
    app_tg = Application.builder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            LANGUAGE: [CallbackQueryHandler(set_language, pattern="^lang_")],
            MENU: [
                CallbackQueryHandler(about, pattern="^about$"),
                CallbackQueryHandler(ai_chat_start, pattern="^ai_chat$")
            ],
            ASK_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_name)],
            ASK_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_phone)],
            ASK_EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_email)],
            ASK_JOB: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_job)],
            AI_CHAT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, ai_chat),
                CommandHandler("menu", menu)
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
