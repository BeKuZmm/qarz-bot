import logging
import os
from datetime import datetime
from dotenv import load_dotenv

from telegram import Update
from telegram.ext import (
    Application, CommandHandler, MessageHandler, CallbackQueryHandler,
    ConversationHandler, filters
)

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

import database as db
from config import *
from handlers.admin import (start, register_name, register_shop,
                             register_password, show_help, cancel)
from handlers.debt import (add_debt_start, debt_name, debt_phone, debt_item,
                            debt_amount, debt_date, show_active_debts,
                            show_paid_debts, debts_menu, paid_callback)
from handlers.client import client_contact, client_my_debts
from handlers.report import show_report, show_clients
from handlers.settings import (settings_menu, reminder_time_start, reminder_time_set,
                                message_template_start, message_template_set,
                                shop_name_start, shop_name_set,
                                password_start, password_old, password_new,
                                back_to_main)
from handlers.reminder import send_reminders

load_dotenv()
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)


def main():
    app = Application.builder().token(BOT_TOKEN).build()

    # ─── CONVERSATION: Ro'yxatdan o'tish ─────────────────
    register_conv = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            REGISTER_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, register_name)],
            REGISTER_SHOP: [MessageHandler(filters.TEXT & ~filters.COMMAND, register_shop)],
            REGISTER_PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, register_password)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        per_message=False
    )

    # ─── CONVERSATION: Qarz qo'shish ─────────────────────
    debt_conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^➕ Yangi qarz qo'shish$"), add_debt_start)],
        states={
            DEBT_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, debt_name)],
            DEBT_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, debt_phone)],
            DEBT_ITEM: [MessageHandler(filters.TEXT & ~filters.COMMAND, debt_item)],
            DEBT_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, debt_amount)],
            DEBT_DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, debt_date)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        per_message=False
    )

    # ─── CONVERSATION: Sozlamalar ─────────────────────────
    settings_conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^⚙️ Sozlamalar$"), settings_menu)],
        states={
            SETTINGS_REMINDER_TIME: [MessageHandler(filters.TEXT & ~filters.COMMAND, reminder_time_set)],
            SETTINGS_MESSAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, message_template_set)],
            SETTINGS_SHOP_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, shop_name_set)],
            SETTINGS_OLD_PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, password_old)],
            SETTINGS_NEW_PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, password_new)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        per_message=False
    )

    # ─── HANDLERLAR ──────────────────────────────────────
    app.add_handler(register_conv)
    app.add_handler(debt_conv)
    app.add_handler(settings_conv)

    # Sozlamalar tugmalari
    app.add_handler(MessageHandler(filters.Regex("^🔔 Eslatma vaqti$"), reminder_time_start))
    app.add_handler(MessageHandler(filters.Regex("^📝 Xabar matni$"), message_template_start))
    app.add_handler(MessageHandler(filters.Regex("^🏪 Do'kon nomi$"), shop_name_start))
    app.add_handler(MessageHandler(filters.Regex("^🔐 Parol o'zgartirish$"), password_start))
    app.add_handler(MessageHandler(filters.Regex("^🔙 Orqaga$"), back_to_main))

    # Admin tugmalari
    app.add_handler(MessageHandler(filters.Regex("^👥 Mijozlar ro'yxati$"), show_clients))
    app.add_handler(MessageHandler(filters.Regex("^💰 Qarzlar ro'yxati$"), debts_menu))
    app.add_handler(MessageHandler(filters.Regex("^📋 Aktiv qarzlar$"), show_active_debts))
    app.add_handler(MessageHandler(filters.Regex("^✅ To'langan qarzlar$"), show_paid_debts))
    app.add_handler(MessageHandler(filters.Regex("^📊 Hisobot$"), show_report))
    app.add_handler(MessageHandler(filters.Regex("^❓ Yordam$"), show_help))

    # Mijoz tugmalari
    app.add_handler(MessageHandler(filters.CONTACT, client_contact))
    app.add_handler(MessageHandler(filters.Regex("^💳 Mening qarzlarim$"), client_my_debts))

    # Callback (To'landi tugmasi)
    app.add_handler(CallbackQueryHandler(paid_callback, pattern="^paid_"))

    # ─── SCHEDULER ───────────────────────────────────────
    scheduler = AsyncIOScheduler()

    async def scheduled_reminder():
        await send_reminders(app.bot)

    # Har kuni 09:00 da (UTC+5 = 04:00 UTC)
    scheduler.add_job(
        scheduled_reminder,
        CronTrigger(hour=4, minute=0),  # UTC 04:00 = O'zbekiston 09:00
        id="daily_reminder"
    )
    scheduler.start()

    # ─── ISHGA TUSHIRISH ─────────────────────────────────
    import asyncio

    async def on_startup(app):
        await db.init_db()
        logger.info("✅ Bot ishga tushdi!")

    app.post_init = on_startup

    logger.info("Bot ishga tushmoqda...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
