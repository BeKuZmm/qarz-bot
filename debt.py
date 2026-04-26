from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes, ConversationHandler
from datetime import datetime
from config import DEBT_NAME, DEBT_PHONE, DEBT_ITEM, DEBT_AMOUNT, DEBT_DATE
import database as db
from handlers.admin import ADMIN_MENU


async def add_debt_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "➕ <b>Yangi qarz qo'shish</b>\n\n"
        "Mijozning ismini kiriting:",
        parse_mode="HTML",
        reply_markup=ReplyKeyboardMarkup([["❌ Bekor qilish"]], resize_keyboard=True)
    )
    return DEBT_NAME


async def debt_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "❌ Bekor qilish":
        return await cancel(update, context)

    context.user_data["debt_name"] = update.message.text.strip()
    await update.message.reply_text("📞 Telefon raqamini kiriting:\n\nMisol: +998901234567")
    return DEBT_PHONE


async def debt_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "❌ Bekor qilish":
        return await cancel(update, context)

    phone = update.message.text.strip()
    context.user_data["debt_phone"] = phone
    await update.message.reply_text("🛍 Nima oldi? (mahsulot nomi):")
    return DEBT_ITEM


async def debt_item(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "❌ Bekor qilish":
        return await cancel(update, context)

    context.user_data["debt_item"] = update.message.text.strip()
    await update.message.reply_text("💰 Qarz summasi (faqat raqam):\n\nMisol: 500000")
    return DEBT_AMOUNT


async def debt_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "❌ Bekor qilish":
        return await cancel(update, context)

    try:
        amount = int(update.message.text.strip().replace(" ", "").replace(",", ""))
        context.user_data["debt_amount"] = amount
        await update.message.reply_text(
            "📅 To'lash sanasini kiriting:\n\nMisol: 30.05.2025"
        )
        return DEBT_DATE
    except ValueError:
        await update.message.reply_text("❌ Faqat raqam kiriting!\n\nMisol: 500000")
        return DEBT_AMOUNT


async def debt_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "❌ Bekor qilish":
        return await cancel(update, context)

    try:
        due_date = datetime.strptime(update.message.text.strip(), "%d.%m.%Y").date()
    except ValueError:
        await update.message.reply_text("❌ Sana noto'g'ri! Format: 30.05.2025")
        return DEBT_DATE

    user_id = update.effective_user.id
    bot_username = context.bot.username

    # Mijozni bazaga qo'shish (yoki mavjudini olish)
    client = await db.get_client_by_phone(context.user_data["debt_phone"], user_id)
    if client:
        client_id = client["id"]
    else:
        client_id = await db.create_client(
            admin_id=user_id,
            name=context.user_data["debt_name"],
            phone=context.user_data["debt_phone"]
        )

    # Qarz qo'shish
    await db.create_debt(
        client_id=client_id,
        admin_id=user_id,
        item=context.user_data["debt_item"],
        amount=context.user_data["debt_amount"],
        due_date=due_date
    )

    # Havola yaratish
    link = f"https://t.me/{bot_username}?start=client_{client_id}"

    await update.message.reply_text(
        f"✅ <b>Qarz qo'shildi!</b>\n\n"
        f"👤 Mijoz: {context.user_data['debt_name']}\n"
        f"📞 Telefon: {context.user_data['debt_phone']}\n"
        f"🛍 Mahsulot: {context.user_data['debt_item']}\n"
        f"💰 Summa: {context.user_data['debt_amount']:,} so'm\n"
        f"📅 To'lash sanasi: {due_date.strftime('%d.%m.%Y')}\n\n"
        f"📲 <b>Mijozga shu havolani yuboring:</b>\n"
        f"{link}",
        parse_mode="HTML",
        reply_markup=ADMIN_MENU
    )
    return ConversationHandler.END


async def show_active_debts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    debts = await db.get_active_debts(user_id)

    if not debts:
        await update.message.reply_text("📭 Aktiv qarzlar yo'q.")
        return

    text = "💰 <b>Aktiv qarzlar:</b>\n\n"
    for i, d in enumerate(debts, 1):
        text += (
            f"{i}. <b>{d['client_name']}</b>\n"
            f"   📞 {d['phone']}\n"
            f"   🛍 {d['item']}\n"
            f"   💰 {d['amount']:,} so'm\n"
            f"   📅 {d['due_date'].strftime('%d.%m.%Y')}\n"
        )

        # To'landi tugmasi
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ To'landi", callback_data=f"paid_{d['id']}")]
        ])

        await update.message.reply_text(
            f"👤 <b>{d['client_name']}</b>\n"
            f"📞 {d['phone']}\n"
            f"🛍 {d['item']}\n"
            f"💰 {d['amount']:,} so'm\n"
            f"📅 {d['due_date'].strftime('%d.%m.%Y')}",
            parse_mode="HTML",
            reply_markup=keyboard
        )


async def show_paid_debts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    debts = await db.get_paid_debts(user_id)

    if not debts:
        await update.message.reply_text("📭 To'langan qarzlar yo'q.")
        return

    text = "✅ <b>To'langan qarzlar:</b>\n\n"
    for i, d in enumerate(debts, 1):
        text += (
            f"{i}. {d['client_name']} — {d['amount']:,} so'm\n"
            f"   🛍 {d['item']} | 📅 {d['paid_at'].strftime('%d.%m.%Y')}\n\n"
        )

    await update.message.reply_text(text, parse_mode="HTML")


async def debts_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "💰 <b>Qarzlar ro'yxati</b>\n\nQaysinisini ko'rmoqchisiz?",
        parse_mode="HTML",
        reply_markup=ReplyKeyboardMarkup([
            ["📋 Aktiv qarzlar", "✅ To'langan qarzlar"],
            ["🔙 Orqaga"]
        ], resize_keyboard=True)
    )


async def paid_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    debt_id = int(query.data.split("_")[1])
    await db.mark_debt_paid(debt_id)

    await query.edit_message_text(
        query.message.text + "\n\n✅ To'landi deb belgilandi!",
        parse_mode="HTML"
    )


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Bekor qilindi.", reply_markup=ADMIN_MENU)
    return ConversationHandler.END
