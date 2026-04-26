import logging
from datetime import datetime
import database as db

logger = logging.getLogger(__name__)


async def send_reminders(bot):
    """Bugun to'lash kerak bo'lgan qarzlar uchun eslatma yuborish"""
    try:
        debts = await db.get_today_debts()

        if not debts:
            logger.info("Bugun to'lanadigan qarz yo'q")
            return

        # Admin bo'yicha guruhlaymiz
        admin_debts = {}
        for debt in debts:
            admin_id = debt["admin_telegram_id"]
            if admin_id not in admin_debts:
                admin_debts[admin_id] = []
            admin_debts[admin_id].append(debt)

        for admin_telegram_id, debts_list in admin_debts.items():

            # ─── ADMINGA XABAR ───────────────────────────────────
            admin_text = f"📌 <b>Bugungi to'lovlar ({datetime.now().strftime('%d.%m.%Y')})</b>\n\n"
            total = 0

            for i, d in enumerate(debts_list, 1):
                admin_text += (
                    f"{i}. <b>{d['client_name']}</b>\n"
                    f"   📞 {d['phone']}\n"
                    f"   🛍 {d['item']}\n"
                    f"   💰 {d['amount']:,} so'm\n\n"
                )
                total += d["amount"]

            admin_text += f"💰 <b>Jami: {total:,} so'm</b>"

            try:
                await bot.send_message(
                    chat_id=admin_telegram_id,
                    text=admin_text,
                    parse_mode="HTML"
                )
            except Exception as e:
                logger.error(f"Admin {admin_telegram_id} ga xabar yuborilmadi: {e}")

            # ─── MIJOZLARGA XABAR ────────────────────────────────
            for debt in debts_list:
                if not debt["telegram_id"]:
                    logger.warning(f"Mijoz {debt['client_name']} Telegram ga ulanmagan")
                    continue

                template = debt["message_template"]
                client_text = template.format(
                    ism=debt["client_name"],
                    summa=f"{debt['amount']:,}",
                    mahsulot=debt["item"],
                    sana=debt["due_date"].strftime("%d.%m.%Y"),
                    dokon=debt["shop_name"]
                )

                try:
                    await bot.send_message(
                        chat_id=debt["telegram_id"],
                        text=client_text
                    )
                    logger.info(f"✅ {debt['client_name']} ga xabar yuborildi")
                except Exception as e:
                    logger.error(f"Mijoz {debt['client_name']} ga xabar yuborilmadi: {e}")

    except Exception as e:
        logger.error(f"Reminder xatolik: {e}")
