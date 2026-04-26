import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")

# Conversation states
(
    # Admin ro'yxatdan o'tish
    REGISTER_NAME,
    REGISTER_SHOP,
    REGISTER_PASSWORD,

    # Login
    LOGIN_PASSWORD,

    # Qarz qo'shish
    DEBT_NAME,
    DEBT_PHONE,
    DEBT_ITEM,
    DEBT_AMOUNT,
    DEBT_DATE,

    # Sozlamalar
    SETTINGS_REMINDER_TIME,
    SETTINGS_MESSAGE,
    SETTINGS_SHOP_NAME,
    SETTINGS_NEW_PASSWORD,
    SETTINGS_OLD_PASSWORD,

) = range(14)
