import os
import sqlite3
from datetime import datetime, timezone
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

DB_PATH = os.getenv("DB_PATH", "bot.db")

def init_db():
    con = sqlite3.connect(DB_PATH)
    con.execute("""CREATE TABLE IF NOT EXISTS signals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        created_at TEXT NOT NULL,
        symbol TEXT,
        result TEXT
    )""")
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
    text = "\n".join(f"{r[0]} | {r[1] or '-'} | {r[2] or '-'}" for r in rows)
    await update.message.reply_text(text)

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    con = sqlite3.connect(DB_PATH)
    total = con.execute("SELECT COUNT(*) FROM signals").fetchone()[0]
    con.close()
    await update.message.reply_text(f"إجمالي السجلات: {total}")

async def today(update: Update, context: ContextTypes.DEFAULT_TYPE):
    today = datetime.now(timezone.utc).date().isoformat()
    con = sqlite3.connect(DB_PATH)
    rows = con.execute(
        "SELECT created_at, symbol, result FROM signals WHERE created_at LIKE ? ORDER BY id DESC",
        (today + "%",)
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
    init_db()
    app = Application.builder().token(token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("history", history))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CommandHandler("today", today))
    app.add_handler(CommandHandler("otc", otc))
    app.run_polling()

if __name__ == "__main__":
    main()
