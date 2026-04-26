from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from telegram.ext import ContextTypes, ConversationHandler
from config import (REGISTER_NAME, REGISTER_SHOP, REGISTER_PASSWORD,
                    LOGIN_PASSWORD)
import database as db


ADMIN_MENU = ReplyKeyboardMarkup([
    ["➕ Yangi qarz qo'shish", "👥 Mijozlar ro'yxati"],
    ["💰 Qarzlar ro'yxati", "📊 Hisobot"],
    ["⚙️ Sozlamalar", "❓ Yordam"]
], resize_keyboard=True)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    args = context.args

    # Mijoz havola orqali kelgan
    if args and args[0].startswith("client_"):
        client_id = int(args[0].split("_")[1])
        context.user_data["client_id"] = client_id
        await update.message.reply_text(
            "Salom! 👋\n\nQarz botiga xush kelibsiz.\n"
            "Telefon raqamingizni yuboring:",
            reply_markup=ReplyKeyboardMarkup([
                [KeyboardButton("📱 Raqamni yuborish", request_contact=True)]
            ], resize_keyboard=True, one_time_keyboard=True)
        )
        return

    # Admin bo'lsa
    if await db.admin_exists(user_id):
        admin = await db.get_admin(user_id)
        await update.message.reply_text(
            f"Xush kelibsiz, {admin['name']}! 👋\n"
            f"🏪 {admin['shop_name']}",
            reply_markup=ADMIN_MENU
        )
        return

    # Yangi admin ro'yxatdan o'tish
    await update.message.reply_text(
        "Salom! 👋\n\nQarz daftari botiga xush kelibsiz.\n\n"
        "Ro'yxatdan o'tish uchun ismingizni kiriting:"
    )
    return REGISTER_NAME


async def register_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["name"] = update.message.text.strip()
    await update.message.reply_text("Do'kon nomini kiriting:")
    return REGISTER_SHOP


async def register_shop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["shop_name"] = update.message.text.strip()
    await update.message.reply_text(
        "Admin parol o'rnating (botga kirish uchun):\n\n"
        "⚠️ Parolni yodda saqlang!"
    )
    return REGISTER_PASSWORD


async def register_password(update: Update, context: ContextTypes.DEFAULT_TYPE):
    password = update.message.text.strip()
    user_id = update.effective_user.id

    await db.create_admin(
        telegram_id=user_id,
        name=context.user_data["name"],
        shop_name=context.user_data["shop_name"],
        password=password
    )

    await update.message.reply_text(
        f"✅ Ro'yxatdan o'tdingiz!\n\n"
        f"👤 Ism: {context.user_data['name']}\n"
        f"🏪 Do'kon: {context.user_data['shop_name']}\n\n"
        f"Boshqaruv paneliga xush kelibsiz!",
        reply_markup=ADMIN_MENU
    )
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "❌ Bekor qilindi.",
        reply_markup=ADMIN_MENU
    )
    return ConversationHandler.END


async def show_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    is_admin = await db.admin_exists(user_id)

    if is_admin:
        text = (
            "❓ <b>Yordam — Admin</b>\n\n"
            "➕ <b>Yangi qarz qo'shish</b> — Mijoz ma'lumoti va qarz kiritish\n"
            "👥 <b>Mijozlar ro'yxati</b> — Barcha mijozlarni ko'rish\n"
            "💰 <b>Qarzlar ro'yxati</b> — Aktiv va to'langan qarzlar\n"
            "📊 <b>Hisobot</b> — Kunlik va umumiy statistika\n"
            "⚙️ <b>Sozlamalar</b> — Eslatma vaqti, xabar matni\n\n"
            "❓ Texnik muammo bo'lsa admin bilan bog'laning."
        )
    else:
        text = (
            "❓ <b>Yordam</b>\n\n"
            "Bu bot orqali siz:\n\n"
            "✅ Qarzingiz haqida eslatma olasiz\n"
            "✅ Qarzlaringizni ko'rishingiz mumkin\n\n"
            "❗️ Muammo bo'lsa do'kon bilan bog'laning."
        )

    await update.message.reply_text(text, parse_mode="HTML")
