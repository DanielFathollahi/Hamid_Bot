import os
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    ConversationHandler, ContextTypes, filters
)
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
GROUP_CHAT_ID = -1002542201765

LANGUAGE, NAME, JOB, PHONE, EMAIL = range(5)

languages = {
    "🇮🇷 فارسی": "fa",
    "🇺🇸 English": "en",
    "🇸🇦 العربية": "ar",
    "🇨🇳 中文": "zh"
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
    reply_keyboard = [[k] for k in languages.keys()]
    await update.message.reply_text(
        "🌐 لطفاً زبان خود را انتخاب کنید / Please select your language:",
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True),
    )
    return LANGUAGE


async def set_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang_choice = update.message.text
    lang = languages.get(lang_choice, "fa")
    context.user_data["lang"] = lang

    await update.message.reply_text(about_us[lang])
    await update.message.reply_text("👤 لطفاً نام و نام خانوادگی‌تان را بفرستید:" if lang == "fa"
                                    else "👤 Please send your full name:")
    return NAME


async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["name"] = update.message.text
    lang = context.user_data["lang"]
    await update.message.reply_text("💼 درباره‌ی شغل خودتان بگویید:" if lang == "fa"
                                    else "💼 Please tell about your job:")
    return JOB


async def get_job(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["job"] = update.message.text
    lang = context.user_data["lang"]
    await update.message.reply_text("📞 شماره تماس خود را وارد کنید:" if lang == "fa"
                                    else "📞 Please enter your phone number:")
    return PHONE


async def get_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["phone"] = update.message.text
    lang = context.user_data["lang"]
    await update.message.reply_text("✉️ ایمیل خود را وارد کنید:" if lang == "fa"
                                    else "✉️ Please enter your email:")
    return EMAIL


async def get_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["email"] = update.message.text
    text = (
        f"👤 {context.user_data['name']}\n"
        f"💼 {context.user_data['job']}\n"
        f"📞 {context.user_data['phone']}\n"
        f"✉️ {context.user_data['email']}\n"
    )
    await context.bot.send_message(chat_id=GROUP_CHAT_ID, text=text)
    lang = context.user_data["lang"]
    await update.message.reply_text("✅ اطلاعات شما با موفقیت ثبت شد. 🙏" if lang == "fa"
                                    else "✅ Your information has been saved. 🙏")
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data.get("lang", "fa")
    await update.message.reply_text("🔙 به منوی اصلی برگشتید. /start" if lang == "fa"
                                    else "🔙 Back to main menu. /start")
    return ConversationHandler.END


def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            LANGUAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_language)],
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)],
            JOB: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_job)],
            PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_phone)],
            EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_email)],
        },
        fallbacks=[MessageHandler(filters.Regex("🔙"), cancel)],
    )

    app.add_handler(conv_handler)

    app.run_webhook(
        listen="0.0.0.0",
        port=int(os.getenv("PORT", 8000)),
        webhook_url=f"https://YOUR_RENDER_URL/{BOT_TOKEN}"
    )


if __name__ == "__main__":
    main()
