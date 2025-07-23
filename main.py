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
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY") or "AIzaSyCrFmZJzTV49AyhrJ-7baN-R7ulkEoUDxw"
GROUP_CHAT_ID = -1002542201765

app = Flask(__name__)

LANGUAGE, MENU, AI_CHAT, ASK_NAME, ASK_JOB, ASK_PHONE, ASK_EMAIL = range(7)

languages = {
    "fa": {"flag": "🇮🇷", "name": "فارسی"},
    "en": {"flag": "🇬🇧", "name": "English"},
    "ar": {"flag": "🇸🇦", "name": "العربية"},
    "zh": {"flag": "🇨🇳", "name": "中文"}
}

about_us = {
    "fa": """... (متن فارسی درباره ما)""",
    "en": """... (English about us text)""",
    "ar": """... (Arabic about us text)""",
    "zh": """... (Chinese about us text)"""
}

user_sessions = {}

@app.route('/')
def ping():
    return 'pong'

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    buttons = [[InlineKeyboardButton(f"{v['flag']} {v['name']}", callback_data=f"lang_{k}")] for k, v in languages.items()]
    await update.message.reply_text("\U0001F310 لطفاً زبان خود را انتخاب کنید:\nPlease select your language:", reply_markup=InlineKeyboardMarkup(buttons))
    return LANGUAGE

async def set_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = update.callback_query.data.split("_")[1]
    context.user_data["lang"] = lang
    user_sessions[update.effective_user.id] = {"count": 0, "date": datetime.now().date()}
    await update.callback_query.answer()
    await show_menu(update, context)
    return MENU

async def show_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data["lang"]
    text = {
        "fa": "📋 لطفاً یکی را انتخاب کنید:",
        "en": "📋 Please choose an option:",
        "ar": "📋 الرجاء اختيار خيار:",
        "zh": "📋 请选择一个选项："
    }[lang]
    buttons = [
        [InlineKeyboardButton({"fa": "📄 درباره ما", "en": "📄 About us", "ar": "📄 عنا", "zh": "📄 关于我们"}[lang], callback_data="about")],
        [InlineKeyboardButton({"fa": "🤖 چت با هوش مصنوعی", "en": "🤖 Chat with AI", "ar": "🤖 الدردشة مع الذكاء الصناعي", "zh": "🤖 与AI聊天"}[lang], callback_data="ai_chat")]
    ]
    await update.callback_query.message.reply_text(text, reply_markup=InlineKeyboardMarkup(buttons))
    return MENU

async def about(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data.get("lang", "fa")
    await update.callback_query.answer()
    await update.callback_query.message.reply_text(about_us[lang])
    prompts = {
        "fa": "✍️ لطفا نام و نام خانوادگی خود را وارد کنید:",
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
        "en": "📧 Your email address?",
        "ar": "📧 بريدك الإلكتروني؟",
        "zh": "📧 您的电子邮箱？"
    }
    await update.message.reply_text(prompts[lang])
    return ASK_EMAIL

async def ask_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["email"] = update.message.text
    lang = context.user_data.get("lang", "fa")
    user = update.effective_user
    text = f"\U0001F4E5 اطلاعات همکاری جدید:\n\n" \
           f"👤 نام: {context.user_data['full_name']}\n" \
           f"💼 شغل: {context.user_data['job']}\n" \
           f"📱 تماس: {context.user_data['phone']}\n" \
           f"📧 ایمیل: {context.user_data['email']}\n" \
           f"🔗 یوزرنیم: @{user.username or '---'}\n" \
           f"🆔 ID: {user.id}"
    await update.message.reply_text({
        "fa": "✅ اطلاعات شما ثبت شد.",
        "en": "✅ Your information has been submitted.",
        "ar": "✅ تم إرسال معلوماتك.",
        "zh": "✅ 您的信息已提交"
    }[lang])
    await context.bot.send_message(chat_id=GROUP_CHAT_ID, text=text)
    return MENU

# (تابع ai_chat و ai_chat_start و cancel مثل قبل باقی می‌مانند)

# main و threading را هم مثل قبل نگه دار
