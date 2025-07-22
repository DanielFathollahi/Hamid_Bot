import os
import threading
from datetime import date
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

genai.configure(api_key=os.environ["GOOGLE_API_KEY"])
model = genai.GenerativeModel("gemini-1.5-flash")

GROUP_CHAT_ID = -1002542201765
ASK_DESCRIPTION, ASK_PHONE = range(2)

app = Flask(__name__)

@app.route('/')
def ping():
    return 'pong'


LANG_FLAGS = {
    "fa": "🇮🇷",
    "en": "🇺🇸",
    "ar": "🇸🇦",
    "zh": "🇨🇳"
}

LANG_NAMES = {
    "fa": "فارسی",
    "en": "English",
    "ar": "العربية",
    "zh": "中文"
}

TEXTS = {
    "lang_select": "🌐 لطفاً زبان / Please select your language / اختر لغتك / 请选择您的语言:",
    "options": {
        "fa": ["📄 درباره من و همکاری با ما", "🤖 چت با هوش مصنوعی"],
        "en": ["📄 About Me and Collaboration", "🤖 Chat with AI"],
        "ar": ["📄 عني والتعاون معنا", "🤖 الدردشة مع الذكاء الاصطناعي"],
        "zh": ["📄 关于我和合作", "🤖 与AI聊天"]
    },
    "intro_about": {
        "fa": "📌 درباره من و همکاری با ما:\nحمید فتح‌اللهی فعال در حوزه پیگمنت‌های معدنی و صادرات محصولات به بازارهای جهانی.",
        "en": "📌 About Me and Collaboration:\nHamid Fathollahi is active in mineral pigments and exporting products worldwide.",
        "ar": "📌 عني والتعاون معنا:\nحميد فتح اللهي نشط في الأصباغ المعدنية وتصدير المنتجات إلى الأسواق العالمية.",
        "zh": "📌 关于我和合作：\n哈米德·法索拉希活跃于矿物颜料领域并向全球市场出口产品。"
    },
    "ask_description": {
        "fa": "✍️ لطفاً درباره‌ی کار خود و خودتان توضیح دهید:",
        "en": "✍️ Please describe your work and yourself:",
        "ar": "✍️ يرجى وصف عملك ونفسك:",
        "zh": "✍️ 请描述您的工作和您自己："
    },
    "ask_phone": {
        "fa": "📞 لطفاً شماره تلفن خود را ارسال کنید:",
        "en": "📞 Please send your phone number:",
        "ar": "📞 يرجى إرسال رقم هاتفك:",
        "zh": "📞 请发送您的电话号码："
    },
    "info_received": {
        "fa": "✅ اطلاعات شما ثبت شد. ممنون 🙏",
        "en": "✅ Your information has been recorded. Thank you 🙏",
        "ar": "✅ تم تسجيل معلوماتك. شكراً 🙏",
        "zh": "✅ 您的信息已被记录。谢谢 🙏"
    },
    "chat_limit_reached": {
        "fa": "🚫 شما به حداکثر ۵ پیام امروز رسیدید.",
        "en": "🚫 You have reached the maximum of 5 messages today.",
        "ar": "🚫 لقد وصلت إلى الحد الأقصى (٥ رسائل) اليوم.",
        "zh": "🚫 您已达到今天允许的最大消息数（5条）。"
    },
    "chat_prompt": {
        "fa": "🤖 می‌توانید تا ۵ پیام با هوش مصنوعی چت کنید. سوال خود را بپرسید:",
        "en": "🤖 You can chat up to 5 times with AI. Please ask your question:",
        "ar": "🤖 يمكنك الدردشة مع الذكاء الاصطناعي حتى ٥ مرات. يرجى طرح سؤالك:",
        "zh": "🤖 您每天最多可与AI聊天5条消息。请提出您的问题："
    },
    "token_denied": {
        "fa": "❌ اجازه ندارم در این مورد صحبت کنم.",
        "en": "❌ I'm not allowed to discuss this.",
        "ar": "❌ لا يسمح لي بالتحدث عن هذا.",
        "zh": "❌ 我不允许讨论此事。"
    },
    "back_to_main": {
        "fa": "🏠 بازگشت به منو",
        "en": "🏠 Back to menu",
        "ar": "🏠 العودة للقائمة",
        "zh": "🏠 返回菜单"
    }
}


def get_text(key, lang):
    return TEXTS.get(key, {}).get(lang, TEXTS.get(key, {}).get("fa", ""))


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton(f"{LANG_FLAGS[code]} {LANG_NAMES[code]}", callback_data=f"lang_{code}")]
        for code in LANG_NAMES
    ]
    await update.message.reply_text(TEXTS["lang_select"], reply_markup=InlineKeyboardMarkup(keyboard))


async def language_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    lang = query.data.split("_")[1]
    context.user_data["lang"] = lang
    await show_main_menu(query.message, lang)


async def show_main_menu(message, lang):
    options = get_text("options", lang)
    keyboard = [
        [InlineKeyboardButton(options[0], callback_data="about_us")],
        [InlineKeyboardButton(options[1], callback_data="chat_ai")]
    ]
    await message.reply_text("👇", reply_markup=InlineKeyboardMarkup(keyboard))


async def about_us(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    lang = context.user_data.get("lang", "fa")

    await query.message.reply_text(get_text("intro_about", lang))
    await query.message.reply_text(get_text("ask_description", lang))
    return ASK_DESCRIPTION


async def ask_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["description"] = update.message.text
    lang = context.user_data.get("lang", "fa")
    keyboard = [[KeyboardButton("📱 ارسال شماره", request_contact=True)]]
    markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    await update.message.reply_text(get_text("ask_phone", lang), reply_markup=markup)
    return ASK_PHONE


async def collect(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    contact = update.message.contact
    phone = contact.phone_number if contact else update.message.text
    description = context.user_data.get("description", "")
    lang = context.user_data.get("lang", "fa")

    msg = (
        f"👤 {user.first_name} {user.last_name or ''}\n"
        f"🆔 {user.id}\n"
        f"🔗 @{user.username or 'ندارد'}\n"
        f"📝 {description}\n"
        f"📞 {phone}"
    )

    await context.bot.send_message(GROUP_CHAT_ID, msg)
    await update.message.reply_text(get_text("info_received", lang), reply_markup=ReplyKeyboardMarkup([], resize_keyboard=True))
    return ConversationHandler.END


def reset_ai_counter_if_new_day(context):
    user_data = context.user_data
    today_str = date.today().isoformat()
    if user_data.get("last_chat_day") != today_str:
        user_data["last_chat_day"] = today_str
        user_data["ai_count"] = 0


async def chat_ai_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    reset_ai_counter_if_new_day(context)
    lang = context.user_data.get("lang", "fa")

    await query.message.reply_text(get_text("chat_prompt", lang))


async def chat_ai(update: Update, context: ContextTypes.DEFAULT_TYPE):
    reset_ai_counter_if_new_day(context)
    count = context.user_data.get("ai_count", 0)
    lang = context.user_data.get("lang", "fa")

    if count >= 5:
        await update.message.reply_text(get_text("chat_limit_reached", lang))
        return

    text = update.message.text.lower()
    trigger_phrases = ["حمید فتح اللهی", "hamid fathollahi", "حميد فتح اللهي", "哈米德"]
    if any(phrase in text for phrase in trigger_phrases):
        await update.message.reply_text(get_text("intro_about", lang))
        return

    if "توکن" in text or "token" in text:
        await update.message.reply_text(get_text("token_denied", lang))
        return

    context.user_data["ai_count"] = count + 1

    response = model.generate_content(text)
    await update.message.reply_text(response.text)

    keyboard = [[InlineKeyboardButton(get_text("back_to_main", lang), callback_data="back_to_main")]]
    await update.message.reply_text("⬅️", reply_markup=InlineKeyboardMarkup(keyboard))


async def back_to_main(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    lang = context.user_data.get("lang", "fa")
    await show_main_menu(query.message, lang)


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
    app_tg.add_handler(CallbackQueryHandler(back_to_main, pattern="back_to_main"))
    app_tg.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat_ai))

    app_tg.run_polling()


if __name__ == "__main__":
    threading.Thread(target=lambda: app.run(host="0.0.0.0", port=8000)).start()
    run_bot()
