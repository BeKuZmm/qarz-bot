from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ContextTypes
from datetime import date
import database as db
from handlers.admin import ADMIN_MENU


async def show_report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    stats = await db.get_stats(user_id)
    today_debts = await db.get_today_debts_for_admin(user_id)

    today_total = sum(d["amount"] for d in today_debts)

    text = (
        f"📊 <b>Hisobot</b>\n\n"
        f"📅 <b>Bugun ({date.today().strftime('%d.%m.%Y')}):</b>\n"
        f"  To'lashi kerak: {len(today_debts)} ta\n"
        f"  Summa: {today_total:,} so'm\n\n"
        f"📈 <b>Umumiy:</b>\n"
        f"  👥 Mijozlar: {stats['clients_count']} ta\n"
        f"  💰 Aktiv qarzlar: {stats['active_count']} ta\n"
        f"  💳 Aktiv summa: {stats['active_total']:,} so'm\n"
        f"  ✅ To'langan: {stats['paid_count']} ta\n"
        f"  💵 To'langan summa: {stats['paid_total']:,} so'm"
    )

    await update.message.reply_text(text, parse_mode="HTML")


async def show_clients(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    clients = await db.get_all_clients(user_id)

    if not clients:
        await update.message.reply_text("👥 Mijozlar yo'q.")
        return

    text = f"👥 <b>Mijozlar ({len(clients)} ta):</b>\n\n"
    for i, c in enumerate(clients, 1):
        linked = "✅" if c["telegram_id"] else "⏳"
        text += f"{i}. {linked} {c['name']} — {c['phone']}\n"

    text += "\n✅ — Telegram ulangan\n⏳ — Havola yuborilmagan"

    await update.message.reply_text(text, parse_mode="HTML")
