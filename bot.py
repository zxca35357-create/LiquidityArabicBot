import os
import sqlite3
from datetime import datetime, timezone

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

DB_PATH = os.getenv("DB_PATH", "bot.db")
PORT = int(os.getenv("PORT", "10000"))
WEBHOOK_PATH = os.getenv("WEBHOOK_PATH", "telegram")


def init_db():
    con = sqlite3.connect(DB_PATH)
    con.execute(
        """CREATE TABLE IF NOT EXISTS signals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            symbol TEXT,
            result TEXT
        )"""
    )
    con.commit()
    con.close()


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "مرحباً بك في البوت.\n\n"
        "الأوامر المتاحة:\n"
        "/history - سجل الإشارات\n"
        "/stats - الإحصائيات\n"
        "/today - نتائج اليوم\n"
        "/otc - قسم OTC"
    )


async def history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    con = sqlite3.connect(DB_PATH)
    rows = con.execute(
        "SELECT created_at, symbol, result FROM signals ORDER BY id DESC LIMIT 10"
    ).fetchall()
    con.close()

    if not rows:
        await update.message.reply_text("لا توجد إشارات مسجلة حالياً.")
        return

    text = "\n".join(
        f"{r[0]} | {r[1] or '-'} | {r[2] or '-'}" for r in rows
    )
    await update.message.reply_text(text)


async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    con = sqlite3.connect(DB_PATH)
    total = con.execute("SELECT COUNT(*) FROM signals").fetchone()[0]
    con.close()
    await update.message.reply_text(f"إجمالي السجلات: {total}")


async def today(update: Update, context: ContextTypes.DEFAULT_TYPE):
    today_date = datetime.now(timezone.utc).date().isoformat()
    con = sqlite3.connect(DB_PATH)
    rows = con.execute(
        "SELECT created_at, symbol, result "
        "FROM signals WHERE created_at LIKE ? ORDER BY id DESC",
        (today_date + "%",),
    ).fetchall()
    con.close()

    if not rows:
        await update.message.reply_text("لا توجد نتائج مسجلة اليوم.")
        return

    await update.message.reply_text(
        "\n".join(f"{r[0]} | {r[1] or '-'} | {r[2] or '-'}" for r in rows)
    )


async def otc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("قسم OTC جاهز للإضافة والتطوير.")


def main():
    token = os.getenv("BOT_TOKEN")
    if not token:
        raise RuntimeError("BOT_TOKEN غير موجود في متغيرات البيئة.")

    external_url = os.getenv("RENDER_EXTERNAL_URL")
    if not external_url:
        raise RuntimeError(
            "RENDER_EXTERNAL_URL غير موجود. شغّل هذا الإصدار كـ Render Web Service."
        )

    init_db()

    app = Application.builder().token(token).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("history", history))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CommandHandler("today", today))
    app.add_handler(CommandHandler("otc", otc))

    webhook_url = f"{external_url.rstrip('/')}/{WEBHOOK_PATH}"

    # Render Free Web Service requires an HTTP listener.
    # Telegram sends updates to this webhook URL.
    app.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path=WEBHOOK_PATH,
        webhook_url=webhook_url,
        drop_pending_updates=True,
    )


if __name__ == "__main__":
    main()
