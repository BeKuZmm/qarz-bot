from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ContextTypes
import database as db


CLIENT_MENU = ReplyKeyboardMarkup([
    ["💳 Mening qarzlarim"],
    ["❓ Yordam"]
], resize_keyboard=True)


async def client_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Mijoz telefon raqamini yuboradi"""
    contact = update.message.contact
    client_id = context.user_data.get("client_id")

    if not client_id:
        await update.message.reply_text(
            "❌ Havola orqali kiring.\n\nDo'kondan maxsus havola oling."
        )
        return

    phone = contact.phone_number
    if not phone.startswith("+"):
        phone = "+" + phone

    # Mijozni Telegram ID bilan ulash
    await db.link_client_telegram(client_id, update.effective_user.id)

    client = await db.get_client_by_id(client_id)

    await update.message.reply_text(
        f"✅ Ro'yxatdan o'tdingiz!\n\n"
        f"👤 {client['name']}\n"
        f"📞 {phone}\n\n"
        f"Endi qarz to'lash kunida sizga eslatma keladi. 🔔",
        reply_markup=CLIENT_MENU
    )


async def client_my_debts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Mijozning qarzlari"""
    user_id = update.effective_user.id

    # Mijozni topish
    conn_row = None
    import asyncpg, os
    conn = await asyncpg.connect(os.getenv("DATABASE_URL"))
    try:
        conn_row = await conn.fetchrow(
            "SELECT * FROM clients WHERE telegram_id = $1", user_id
        )
    finally:
        await conn.close()

    if not conn_row:
        await update.message.reply_text(
            "❌ Siz ro'yxatdan o'tmagansiz.\n\nDo'kondan maxsus havola oling."
        )
        return

    debts = await db.get_client_debts(conn_row["id"])

    if not debts:
        await update.message.reply_text("✅ Qarzingiz yo'q!")
        return

    text = "💳 <b>Sizning qarzlaringiz:</b>\n\n"
    total = 0
    for i, d in enumerate(debts, 1):
        text += (
            f"{i}. 🛍 {d['item']}\n"
            f"   💰 {d['amount']:,} so'm\n"
            f"   📅 To'lash: {d['due_date'].strftime('%d.%m.%Y')}\n\n"
        )
        total += d["amount"]

    text += f"💰 <b>Jami: {total:,} so'm</b>"

    await update.message.reply_text(text, parse_mode="HTML")
