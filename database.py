import os
import asyncpg
from datetime import date


async def get_db():
    return await asyncpg.connect(os.getenv("DATABASE_URL"))


async def init_db():
    conn = await get_db()
    try:
        # Adminlar jadvali
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS admins (
                id SERIAL PRIMARY KEY,
                telegram_id BIGINT UNIQUE NOT NULL,
                name TEXT,
                shop_name TEXT,
                password TEXT,
                reminder_time TEXT DEFAULT '09:00',
                message_template TEXT DEFAULT 'Salom, {ism}! Bugun {summa} so''m qarzingizni to''lash kuni. Do''kon: {dokon}',
                created_at TIMESTAMP DEFAULT NOW()
            )
        """)

        # Mijozlar jadvali
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS clients (
                id SERIAL PRIMARY KEY,
                admin_id BIGINT NOT NULL,
                name TEXT NOT NULL,
                phone TEXT NOT NULL,
                telegram_id BIGINT,
                created_at TIMESTAMP DEFAULT NOW()
            )
        """)

        # Qarzlar jadvali
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS debts (
                id SERIAL PRIMARY KEY,
                client_id INTEGER REFERENCES clients(id) ON DELETE CASCADE,
                admin_id BIGINT NOT NULL,
                item TEXT NOT NULL,
                amount BIGINT NOT NULL,
                due_date DATE NOT NULL,
                is_paid BOOLEAN DEFAULT FALSE,
                paid_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT NOW()
            )
        """)

        print("✅ Jadvallar tayyor")
    finally:
        await conn.close()


# ─── ADMIN ───────────────────────────────────────────────

async def admin_exists(telegram_id: int) -> bool:
    conn = await get_db()
    try:
        row = await conn.fetchrow(
            "SELECT id FROM admins WHERE telegram_id = $1", telegram_id
        )
        return row is not None
    finally:
        await conn.close()


async def create_admin(telegram_id: int, name: str, shop_name: str, password: str):
    conn = await get_db()
    try:
        await conn.execute(
            """INSERT INTO admins (telegram_id, name, shop_name, password)
               VALUES ($1, $2, $3, $4)
               ON CONFLICT (telegram_id) DO NOTHING""",
            telegram_id, name, shop_name, password
        )
    finally:
        await conn.close()


async def get_admin(telegram_id: int):
    conn = await get_db()
    try:
        return await conn.fetchrow(
            "SELECT * FROM admins WHERE telegram_id = $1", telegram_id
        )
    finally:
        await conn.close()


async def check_admin_password(telegram_id: int, password: str) -> bool:
    conn = await get_db()
    try:
        row = await conn.fetchrow(
            "SELECT id FROM admins WHERE telegram_id = $1 AND password = $2",
            telegram_id, password
        )
        return row is not None
    finally:
        await conn.close()


async def update_admin_settings(telegram_id: int, reminder_time: str = None,
                                 message_template: str = None, shop_name: str = None):
    conn = await get_db()
    try:
        if reminder_time:
            await conn.execute(
                "UPDATE admins SET reminder_time = $1 WHERE telegram_id = $2",
                reminder_time, telegram_id
            )
        if message_template:
            await conn.execute(
                "UPDATE admins SET message_template = $1 WHERE telegram_id = $2",
                message_template, telegram_id
            )
        if shop_name:
            await conn.execute(
                "UPDATE admins SET shop_name = $1 WHERE telegram_id = $2",
                shop_name, telegram_id
            )
    finally:
        await conn.close()


async def update_admin_password(telegram_id: int, new_password: str):
    conn = await get_db()
    try:
        await conn.execute(
            "UPDATE admins SET password = $1 WHERE telegram_id = $2",
            new_password, telegram_id
        )
    finally:
        await conn.close()


async def get_all_admins():
    conn = await get_db()
    try:
        return await conn.fetch("SELECT * FROM admins")
    finally:
        await conn.close()


# ─── MIJOZ ───────────────────────────────────────────────

async def create_client(admin_id: int, name: str, phone: str) -> int:
    conn = await get_db()
    try:
        row = await conn.fetchrow(
            """INSERT INTO clients (admin_id, name, phone)
               VALUES ($1, $2, $3) RETURNING id""",
            admin_id, name, phone
        )
        return row["id"]
    finally:
        await conn.close()


async def get_client_by_id(client_id: int):
    conn = await get_db()
    try:
        return await conn.fetchrow(
            "SELECT * FROM clients WHERE id = $1", client_id
        )
    finally:
        await conn.close()


async def get_client_by_phone(phone: str, admin_id: int):
    conn = await get_db()
    try:
        return await conn.fetchrow(
            "SELECT * FROM clients WHERE phone = $1 AND admin_id = $2",
            phone, admin_id
        )
    finally:
        await conn.close()


async def link_client_telegram(client_id: int, telegram_id: int):
    conn = await get_db()
    try:
        await conn.execute(
            "UPDATE clients SET telegram_id = $1 WHERE id = $2",
            telegram_id, client_id
        )
    finally:
        await conn.close()


async def get_all_clients(admin_id: int):
    conn = await get_db()
    try:
        return await conn.fetch(
            "SELECT * FROM clients WHERE admin_id = $1 ORDER BY name", admin_id
        )
    finally:
        await conn.close()


# ─── QARZ ────────────────────────────────────────────────

async def create_debt(client_id: int, admin_id: int, item: str,
                       amount: int, due_date: date) -> int:
    conn = await get_db()
    try:
        row = await conn.fetchrow(
            """INSERT INTO debts (client_id, admin_id, item, amount, due_date)
               VALUES ($1, $2, $3, $4, $5) RETURNING id""",
            client_id, admin_id, item, amount, due_date
        )
        return row["id"]
    finally:
        await conn.close()


async def get_active_debts(admin_id: int):
    conn = await get_db()
    try:
        return await conn.fetch(
            """SELECT d.*, c.name as client_name, c.phone, c.telegram_id
               FROM debts d
               JOIN clients c ON d.client_id = c.id
               WHERE d.admin_id = $1 AND d.is_paid = FALSE
               ORDER BY d.due_date""",
            admin_id
        )
    finally:
        await conn.close()


async def get_paid_debts(admin_id: int):
    conn = await get_db()
    try:
        return await conn.fetch(
            """SELECT d.*, c.name as client_name, c.phone
               FROM debts d
               JOIN clients c ON d.client_id = c.id
               WHERE d.admin_id = $1 AND d.is_paid = TRUE
               ORDER BY d.paid_at DESC""",
            admin_id
        )
    finally:
        await conn.close()


async def get_client_debts(client_id: int):
    conn = await get_db()
    try:
        return await conn.fetch(
            """SELECT * FROM debts
               WHERE client_id = $1 AND is_paid = FALSE
               ORDER BY due_date""",
            client_id
        )
    finally:
        await conn.close()


async def mark_debt_paid(debt_id: int):
    conn = await get_db()
    try:
        await conn.execute(
            """UPDATE debts SET is_paid = TRUE, paid_at = NOW()
               WHERE id = $1""",
            debt_id
        )
    finally:
        await conn.close()


async def get_today_debts():
    """Bugun to'lash kerak bo'lgan barcha qarzlar (barcha adminlar uchun)"""
    conn = await get_db()
    try:
        return await conn.fetch(
            """SELECT d.*, c.name as client_name, c.phone, c.telegram_id,
                      a.shop_name, a.telegram_id as admin_telegram_id,
                      a.message_template
               FROM debts d
               JOIN clients c ON d.client_id = c.id
               JOIN admins a ON d.admin_id = a.id
               WHERE d.due_date = $1 AND d.is_paid = FALSE""",
            date.today()
        )
    finally:
        await conn.close()


async def get_today_debts_for_admin(admin_id: int):
    conn = await get_db()
    try:
        return await conn.fetch(
            """SELECT d.*, c.name as client_name, c.phone, c.telegram_id
               FROM debts d
               JOIN clients c ON d.client_id = c.id
               WHERE d.admin_id = $1 AND d.due_date = $2 AND d.is_paid = FALSE""",
            admin_id, date.today()
        )
    finally:
        await conn.close()


async def get_stats(admin_id: int):
    conn = await get_db()
    try:
        total = await conn.fetchrow(
            """SELECT COUNT(*) as count, COALESCE(SUM(amount), 0) as total
               FROM debts WHERE admin_id = $1 AND is_paid = FALSE""",
            admin_id
        )
        paid = await conn.fetchrow(
            """SELECT COUNT(*) as count, COALESCE(SUM(amount), 0) as total
               FROM debts WHERE admin_id = $1 AND is_paid = TRUE""",
            admin_id
        )
        clients_count = await conn.fetchrow(
            "SELECT COUNT(*) as count FROM clients WHERE admin_id = $1",
            admin_id
        )
        return {
            "active_count": total["count"],
            "active_total": total["total"],
            "paid_count": paid["count"],
            "paid_total": paid["total"],
            "clients_count": clients_count["count"]
        }
    finally:
        await conn.close()
