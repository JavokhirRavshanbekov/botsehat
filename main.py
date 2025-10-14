
import os
import random
from dotenv import load_dotenv
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    ContextTypes,
    filters,
)

# ================== ENV SETUP ==================
load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))
PHOTO_STATE = 18

if not TOKEN:
    raise ValueError("❌ BOT_TOKEN не найден. Проверь .env файл.")

# ================== QUESTIONS ==================
questions = [
    "Ismi Familiyasi:",
    "Tug‘ilgan yili:",
    "Telefon (+998):",
    "Sohangizni tanlang:",
    "To‘liq manzili:",
    "Millati:",
    "Ma'lumoti:",
    "Oilaviy holati:",
    "Tajribangiz haqida yozing:",
    "Oldingi ish joyingizni yozing:",
    "Excel, Word bilish darajasi (0-100%):",
    "Til bilish darajasi Rus, Eng:",
    "Shaxsiy mashinagiz bormi:",
    "Qancha maoshga ishlamoqchisiz?",
    "Qancha vaqt ishlamoqchisiz?",
    "Sudlanganmisiz?",
    "Telegram username'ingizni kiriting @xxxx:",
    "Qayerdan eshitdingiz?",
    "Iltimos, rasimingizni yuboring: (rasimingizni yubormasangiz ariza qabul qilinmaydi!)"
]

variant_keyboards = {
    3: ReplyKeyboardMarkup([["Registratura xodimi", "Hamshira ( kunduzgi va navbatchilikka)"],
                            ["Call center operator"],
                            ["Farrosh"]], resize_keyboard=True),
    5: ReplyKeyboardMarkup([["O'zbek", "Rus"], ["Boshqa millat"]], resize_keyboard=True),
    6: ReplyKeyboardMarkup([["Oliy", "O‘rta"], ["Texnikum", "O‘qiyapman"]], resize_keyboard=True),
    7: ReplyKeyboardMarkup([["Turmush qurgan", "Turmush qurmagan"]], resize_keyboard=True),
    12: ReplyKeyboardMarkup([["Ha", "Yo‘q"]], resize_keyboard=True),
    15: ReplyKeyboardMarkup([["Ha", "Yo‘q"]], resize_keyboard=True),
}

# ================== HANDLERS ==================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начало анкеты или повторный /start перезапускает анкету"""
    context.user_data.clear()  # очищаем предыдущие данные
    context.user_data["step"] = 0
    await update.message.reply_text(
        "Assalomu alaykum! Ro‘yxatdan o‘tish uchun kerakli ma’lumotlarni yuboring.",
        reply_markup=ReplyKeyboardRemove()
    )
    await ask_question(update, context)
    return 1

async def ask_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    step = context.user_data["step"]
    if step in variant_keyboards:
        await update.message.reply_text(questions[step], reply_markup=variant_keyboards[step])
    elif step == PHOTO_STATE:
        await update.message.reply_text(questions[step], reply_markup=ReplyKeyboardRemove())
        return PHOTO_STATE
    else:
        await update.message.reply_text(questions[step], reply_markup=ReplyKeyboardRemove())

async def handle_response(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        await update.message.reply_text("Iltimos, faqat matn yuboring.")
        return 1

    step = context.user_data["step"]
    context.user_data[f"answer_{step}"] = update.message.text
    context.user_data["step"] += 1

    if context.user_data["step"] == PHOTO_STATE:
        await ask_question(update, context)
        return PHOTO_STATE
    elif context.user_data["step"] >= len(questions):
        return await finish(update, context)
    else:
        await ask_question(update, context)
        return 1

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.photo:
        await update.message.reply_text("Iltimos, faqat rasm yuboring.")
        return PHOTO_STATE

    context.user_data["photo"] = update.message.photo[-1].file_id
    return await finish(update, context)

async def finish(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = context.user_data
    anketa_id = f"#{random.randint(10000, 99999)}"
    username = data.get("answer_16", "@no_username")
    photo_id = data.get("photo", None)

    text = (
        f"{anketa_id} ✅ Yangi ariza:\n\n"
        + "\n".join([f"{questions[i]} {data.get(f'answer_{i}', '-')}" for i in range(PHOTO_STATE)])
        + f"\nUsername: {username}\nRasm: {'✅ ilova qilingan' if photo_id else 'yo‘q'}"
    )

    await context.bot.send_message(chat_id=ADMIN_ID, text=text)
    if photo_id:
        await context.bot.send_photo(chat_id=ADMIN_ID, photo=photo_id)

    await update.message.reply_text("✅ Arizangiz yuborildi. Rahmat!", reply_markup=ReplyKeyboardRemove())
    context.user_data.clear()  # очищаем данные после завершения
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Bekor qilindi.", reply_markup=ReplyKeyboardRemove())
    context.user_data.clear()
    return ConversationHandler.END

# ================== MAIN ==================
if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            1: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_response)],
            PHOTO_STATE: [MessageHandler(filters.PHOTO, handle_photo)]
        },
        fallbacks=[CommandHandler("cancel", cancel), CommandHandler("start", start)]
    )

    app.add_handler(conv_handler)
    print("🤖 Bot ishlayapti...")
    app.run_polling()
