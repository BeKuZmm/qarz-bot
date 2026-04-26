from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from config import (SETTINGS_REMINDER_TIME, SETTINGS_MESSAGE,
                    SETTINGS_SHOP_NAME, SETTINGS_NEW_PASSWORD, SETTINGS_OLD_PASSWORD)
import database as db
from handlers.admin import ADMIN_MENU


SETTINGS_MENU = ReplyKeyboardMarkup([
    ["🔔 Eslatma vaqti", "📝 Xabar matni"],
    ["🏪 Do'kon nomi", "🔐 Parol o'zgartirish"],
    ["🔙 Orqaga"]
], resize_keyboard=True)


async def settings_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    admin = await db.get_admin(user_id)

    await update.message.reply_text(
        f"⚙️ <b>Sozlamalar</b>\n\n"
        f"🏪 Do'kon: {admin['shop_name']}\n"
        f"🔔 Eslatma vaqti: {admin['reminder_time']}\n\n"
        f"Nima o'zgartirmoqchisiz?",
        parse_mode="HTML",
        reply_markup=SETTINGS_MENU
    )


# ─── ESLATMA VAQTI ───────────────────────────────────────

async def reminder_time_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🔔 Eslatma vaqtini kiriting:\n\n"
        "Format: 09:00\n"
        "Misol: 08:30, 10:00, 14:00",
        reply_markup=ReplyKeyboardMarkup([["❌ Bekor qilish"]], resize_keyboard=True)
    )
    return SETTINGS_REMINDER_TIME


async def reminder_time_set(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "❌ Bekor qilish":
        await update.message.reply_text("❌ Bekor qilindi.", reply_markup=SETTINGS_MENU)
        return ConversationHandler.END

    time_str = update.message.text.strip()
    try:
        hour, minute = map(int, time_str.split(":"))
        assert 0 <= hour <= 23 and 0 <= minute <= 59
    except:
        await update.message.reply_text("❌ Noto'g'ri format! Misol: 09:00")
        return SETTINGS_REMINDER_TIME

    await db.update_admin_settings(update.effective_user.id, reminder_time=time_str)
    await update.message.reply_text(
        f"✅ Eslatma vaqti {time_str} ga o'zgartirildi!",
        reply_markup=SETTINGS_MENU
    )
    return ConversationHandler.END


# ─── XABAR MATNI ─────────────────────────────────────────

async def message_template_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📝 Mijozga keteydigan xabar matnini kiriting:\n\n"
        "Quyidagi o'zgaruvchilardan foydalanishingiz mumkin:\n"
        "  {ism} — mijoz ismi\n"
        "  {summa} — qarz summasi\n"
        "  {mahsulot} — nima olgani\n"
        "  {sana} — to'lash sanasi\n"
        "  {dokon} — do'kon nomi\n\n"
        "Misol:\n"
        "Salom, {ism}! Bugun {summa} so'm qarzingizni to'lash kuni. Do'kon: {dokon}",
        reply_markup=ReplyKeyboardMarkup([["❌ Bekor qilish"]], resize_keyboard=True)
    )
    return SETTINGS_MESSAGE


async def message_template_set(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "❌ Bekor qilish":
        await update.message.reply_text("❌ Bekor qilindi.", reply_markup=SETTINGS_MENU)
        return ConversationHandler.END

    template = update.message.text.strip()
    await db.update_admin_settings(update.effective_user.id, message_template=template)
    await update.message.reply_text(
        "✅ Xabar matni yangilandi!",
        reply_markup=SETTINGS_MENU
    )
    return ConversationHandler.END


# ─── DO'KON NOMI ─────────────────────────────────────────

async def shop_name_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🏪 Yangi do'kon nomini kiriting:",
        reply_markup=ReplyKeyboardMarkup([["❌ Bekor qilish"]], resize_keyboard=True)
    )
    return SETTINGS_SHOP_NAME


async def shop_name_set(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "❌ Bekor qilish":
        await update.message.reply_text("❌ Bekor qilindi.", reply_markup=SETTINGS_MENU)
        return ConversationHandler.END

    shop_name = update.message.text.strip()
    await db.update_admin_settings(update.effective_user.id, shop_name=shop_name)
    await update.message.reply_text(
        f"✅ Do'kon nomi '{shop_name}' ga o'zgartirildi!",
        reply_markup=SETTINGS_MENU
    )
    return ConversationHandler.END


# ─── PAROL ───────────────────────────────────────────────

async def password_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🔐 Eski parolni kiriting:",
        reply_markup=ReplyKeyboardMarkup([["❌ Bekor qilish"]], resize_keyboard=True)
    )
    return SETTINGS_OLD_PASSWORD


async def password_old(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "❌ Bekor qilish":
        await update.message.reply_text("❌ Bekor qilindi.", reply_markup=SETTINGS_MENU)
        return ConversationHandler.END

    user_id = update.effective_user.id
    old_password = update.message.text.strip()

    is_correct = await db.check_admin_password(user_id, old_password)
    if not is_correct:
        await update.message.reply_text("❌ Parol noto'g'ri! Qaytadan urinib ko'ring.")
        return SETTINGS_OLD_PASSWORD

    await update.message.reply_text("✅ To'g'ri! Yangi parolni kiriting:")
    return SETTINGS_NEW_PASSWORD


async def password_new(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "❌ Bekor qilish":
        await update.message.reply_text("❌ Bekor qilindi.", reply_markup=SETTINGS_MENU)
        return ConversationHandler.END

    new_password = update.message.text.strip()
    await db.update_admin_password(update.effective_user.id, new_password)
    await update.message.reply_text(
        "✅ Parol muvaffaqiyatli o'zgartirildi!",
        reply_markup=SETTINGS_MENU
    )
    return ConversationHandler.END


async def back_to_main(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🏠 Asosiy menyu", reply_markup=ADMIN_MENU)
