import os
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardRemove
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    ConversationHandler,
    filters
)
import google.generativeai as genai

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
genai.configure(api_key=GOOGLE_API_KEY)

model = genai.GenerativeModel("gemini-pro")

GROUP_ID = -1002542201765

LANGUAGE, MENU, AI_CHAT, NAME, JOB, PHONE, EMAIL = range(7)

languages = {
    'fa': '🇮🇷 فارسی',
    'en': '🇬🇧 English',
    'ar': '🇸🇦 العربية',
    'zh': '🇨🇳 中文'
}

about_us = {
    'fa': "📌 معرفی: حمید فتح‌اللهی\n\n"
          "سلام و خوش‌آمدید 🌟\n"
          "من حمید فتح‌اللهی هستم، فعال در حوزه تولید و عرضه انواع پیگمنت‌های معدنی قابل استفاده در:\n"
          "🎨 سفال، سرامیک، فلز، شیشه و سیمان\n"
          "همچنین:\n🌏 واردکننده محصولات از کشورهای شرقی\n🚢 صادرکننده به بازارهای عربی و غربی\n"
          "✨ محصولات ما شامل:\n🏗️ مصالح ساختمانی\n🌱 محصولات کشاورزی\n💎 مواد اولیه صنعت طلا\n🖨️ جوهرهای چاپ دیجیتال",
    'en': "📌 Introduction: Hamid Fathollahi\n\n"
          "Welcome 🌟\n"
          "I am Hamid Fathollahi, active in the production and supply of various mineral pigments for:\n"
          "🎨 pottery, ceramics, metal, glass, and cement\n"
          "Also:\n🌏 importer from Eastern countries\n🚢 exporter to Arab and Western markets\n"
          "✨ Our products include:\n🏗️ building materials\n🌱 agricultural products\n💎 raw materials for the gold industry\n🖨️ digital printing inks",
    'ar': "📌 تقديم: حميد فتح اللهي\n\n"
          "مرحبا بكم 🌟\n"
          "أنا حميد فتح اللهي، ناشط في إنتاج وتوريد أصباغ معدنية مختلفة تستخدم في:\n"
          "🎨 الفخار، السيراميك، المعادن، الزجاج والأسمنت\n"
          "كذلك:\n🌏 مستورد من البلدان الشرقية\n🚢 ومصدر إلى الأسواق العربية والغربية\n"
          "✨ تشمل منتجاتنا:\n🏗️ مواد البناء\n🌱 المنتجات الزراعية\n💎 المواد الخام لصناعة الذهب\n🖨️ أحبار الطباعة الرقمية",
    'zh': "📌 介绍: Hamid Fathollahi\n\n"
          "欢迎 🌟\n"
          "我是 Hamid Fathollahi，活跃于生产和供应各种矿物颜料，适用于：\n"
          "🎨 陶瓷、金属、玻璃和水泥\n"
          "同时：\n🌏 从东方国家进口\n🚢 向阿拉伯和西方市场出口\n"
          "✨ 我们的产品包括：\n🏗️ 建筑材料\n🌱 农产品\n💎 黄金行业的原材料\n🖨️ 数码打印墨水"
}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton(v, callback_data=k)] for k, v in languages.items()
    ]
    await update.message.reply_text("🌐 لطفا زبان را انتخاب کنید:", reply_markup=InlineKeyboardMarkup(keyboard))
    return LANGUAGE

async def language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data['lang'] = query.data
    return await show_menu(query, context)

async def show_menu(query, context):
    lang = context.user_data['lang']
    keyboard = [
        [InlineKeyboardButton("🤝 درباره‌ی من و همکاری با ما", callback_data='about')],
        [InlineKeyboardButton("🧠 چت با هوش مصنوعی", callback_data='chat')]
    ]
    await query.edit_message_text("🏠 منوی اصلی:", reply_markup=InlineKeyboardMarkup(keyboard))
    return MENU

async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == 'about':
        await query.edit_message_text(about_us[context.user_data['lang']])
        await query.message.reply_text("📝 نام و نام خانوادگی خود را وارد کنید:", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 منوی اصلی", callback_data='back')]]))
        return NAME
    elif query.data == 'chat':
        await query.edit_message_text("💬 پیام خود را بنویسید:", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 منوی اصلی", callback_data='back')]]))
        return AI_CHAT

async def back(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    return await show_menu(query, context)

async def ai_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if 'حمید فتح اللهی' in text:
        await update.message.reply_text(about_us[context.user_data['lang']])
        return AI_CHAT
    response = model.generate_content(text).text
    await update.message.reply_text(f"🤖 {response}")
    return AI_CHAT

async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['name'] = update.message.text
    await update.message.reply_text("💼 درباره شغل خود توضیح دهید:")
    return JOB

async def get_job(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['job'] = update.message.text
    await update.message.reply_text("📱 شماره تماس خود را وارد کنید:")
    return PHONE

async def get_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['phone'] = update.message.text
    await update.message.reply_text("📧 ایمیل خود را وارد کنید:")
    return EMAIL

async def get_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['email'] = update.message.text
    info = (f"👤 نام: {context.user_data['name']}\n"
            f"💼 شغل: {context.user_data['job']}\n"
            f"📱 شماره: {context.user_data['phone']}\n"
            f"📧 ایمیل: {context.user_data['email']}")
    await context.bot.send_message(chat_id=GROUP_ID, text=info)
    await update.message.reply_text("✅ اطلاعات شما با موفقیت ارسال شد.")
    return ConversationHandler.END

if __name__ == '__main__':
    app = ApplicationBuilder().token(os.getenv("BOT_TOKEN")).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            LANGUAGE: [CallbackQueryHandler(language)],
            MENU: [CallbackQueryHandler(menu, pattern='^(about|chat)$'),
                   CallbackQueryHandler(back, pattern='back')],
            AI_CHAT: [MessageHandler(filters.TEXT & ~filters.COMMAND, ai_chat),
                      CallbackQueryHandler(back, pattern='back')],
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)],
            JOB: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_job)],
            PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_phone)],
            EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_email)]
        },
        fallbacks=[]
    )

    app.add_handler(conv_handler)
    app.run_polling()
