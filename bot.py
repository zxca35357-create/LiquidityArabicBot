import os
import sqlite3
import asyncio
import math
from datetime import datetime, timezone

import aiohttp
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

# =========================
# SETTINGS
# =========================

DB_PATH = os.getenv("DB_PATH", "bot.db")
PORT = int(os.getenv("PORT", "10000"))
WEBHOOK_PATH = os.getenv("WEBHOOK_PATH", "/telegram")

OTC_API_KEY = os.getenv("OTCHARTS_API_KEY", "")
OTC_BASE_URL = os.getenv("OTCHARTS_BASE_URL", "https://otcharts.com")

VENUE = os.getenv("OTC_VENUE", "otc")

# minimum score required for a signal
SIGNAL_SCORE = int(os.getenv("SIGNAL_SCORE", "8"))

# =========================
# DATABASE
# =========================

def init_db():
    con = sqlite3.connect(DB_PATH)

    con.execute("""
        CREATE TABLE IF NOT EXISTS signals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            symbol TEXT NOT NULL,
            timeframe TEXT NOT NULL,
            direction TEXT NOT NULL,
            confidence INTEGER NOT NULL,
            score INTEGER NOT NULL
        )
    """)

    con.commit()
    con.close()


def save_signal(symbol, timeframe, direction, confidence, score):
    con = sqlite3.connect(DB_PATH)

    con.execute(
        """
        INSERT INTO signals
        (created_at, symbol, timeframe, direction, confidence, score)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            datetime.now(timezone.utc).isoformat(),
            symbol,
            timeframe,
            direction,
            confidence,
            score,
        ),
    )

    con.commit()
    con.close()


# =========================
# OTC API
# =========================

async def api_get(path, params=None):
    if not OTC_API_KEY:
        raise RuntimeError(
            "OTCHARTS_API_KEY غير موجود في Environment Variables."
        )

    headers = {
        "Authorization": f"Bearer {OTC_API_KEY}",
        "Accept": "application/json",
    }

    url = OTC_BASE_URL.rstrip("/") + path

    timeout = aiohttp.ClientTimeout(total=20)

    async with aiohttp.ClientSession(timeout=timeout) as session:
        async with session.get(
            url,
            headers=headers,
            params=params or {},
        ) as response:

            text = await response.text()

            if response.status != 200:
                raise RuntimeError(
                    f"OTC API HTTP {response.status}: {text[:300]}"
                )

            try:
                import json
                return json.loads(text)
            except Exception:
                raise RuntimeError("OTC API رجع بيانات غير صالحة.")


async def get_symbols():
    data = await api_get("/v1/symbols")

    # Current OTCharts response normally contains venues.
    venues = data.get("venues", [])

    for venue in venues:
        if venue.get("id") == VENUE:
            instruments = venue.get("instruments")

            if instruments:
                result = []

                for item in instruments:
                    if isinstance(item, str):
                        result.append(item)
                    elif isinstance(item, dict):
                        symbol = item.get("symbol")
                        if symbol:
                            result.append(symbol)

                return result

    # Some API responses may expose symbols differently.
    symbols = data.get("symbols", [])

    result = []

    for item in symbols:
        if isinstance(item, str):
            result.append(item)
        elif isinstance(item, dict):
            symbol = item.get("symbol")
            if symbol:
                result.append(symbol)

    return result


async def get_candles(symbol, timeframe_seconds, limit=300):
    data = await api_get(
        "/v1/candles",
        {
            "venue": VENUE,
            "symbol": symbol,
            "tf": timeframe_seconds,
            "limit": limit,
        },
    )

    candles = data.get("candles", [])

    cleaned = []

    for c in candles:
        try:
            cleaned.append({
                "open": float(c["open"]),
                "high": float(c["high"]),
                "low": float(c["low"]),
                "close": float(c["close"]),
                "time": int(c["time"]),
                "volume": float(c.get("volume", 0)),
            })
        except Exception:
            continue

    return cleaned


# =========================
# TECHNICAL INDICATORS
# =========================

def ema(values, period):
    if len(values) < period:
        return None

    multiplier = 2 / (period + 1)

    current = sum(values[:period]) / period

    for price in values[period:]:
        current = (
            (price - current) * multiplier
        ) + current

    return current


def rsi(values, period=14):
    if len(values) < period + 1:
        return None

    gains = []
    losses = []

    for i in range(1, len(values)):
        change = values[i] - values[i - 1]

        gains.append(max(change, 0))
        losses.append(max(-change, 0))

    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period

    for i in range(period, len(gains)):
        avg_gain = ((avg_gain * (period - 1)) + gains[i]) / period
        avg_loss = ((avg_loss * (period - 1)) + losses[i]) / period

    if avg_loss == 0:
        return 100.0

    rs = avg_gain / avg_loss

    return 100 - (100 / (1 + rs))


def macd(values):
    if len(values) < 35:
        return None, None

    fast = ema(values, 12)
    slow = ema(values, 26)

    if fast is None or slow is None:
        return None, None

    # Approximation of MACD line from latest EMA values.
    macd_line = fast - slow

    return macd_line, None


def bollinger(values, period=20, deviation=2):
    if len(values) < period:
        return None, None, None

    recent = values[-period:]

    middle = sum(recent) / period

    variance = sum(
        (x - middle) ** 2
        for x in recent
    ) / period

    std = math.sqrt(variance)

    upper = middle + deviation * std
    lower = middle - deviation * std

    return upper, middle, lower


def atr(candles, period=14):
    if len(candles) < period + 1:
        return None

    trs = []

    for i in range(1, len(candles)):
        current = candles[i]
        previous = candles[i - 1]

        tr = max(
            current["high"] - current["low"],
            abs(current["high"] - previous["close"]),
            abs(current["low"] - previous["close"]),
        )

        trs.append(tr)

    if len(trs) < period:
        return None

    return sum(trs[-period:]) / period


def support_resistance(candles, lookback=40):
    if len(candles) < 10:
        return None, None

    recent = candles[-lookback:]

    support = min(c["low"] for c in recent)
    resistance = max(c["high"] for c in recent)

    return support, resistance


# =========================
# ANALYSIS
# =========================

def analyze(candles):
    if len(candles) < 80:
        return {
            "direction": "WAIT",
            "score": 0,
            "confidence": 0,
            "reason": "عدد الشموع غير كافٍ للتحليل."
        }

    closes = [c["close"] for c in candles]

    price = closes[-1]

    ema20 = ema(closes, 20)
    ema50 = ema(closes, 50)
    ema200 = ema(closes, 200)

    current_rsi = rsi(closes, 14)

    macd_line, _ = macd(closes)

    upper, middle, lower = bollinger(closes)

    current_atr = atr(candles, 14)

    support, resistance = support_resistance(candles)

    score_call = 0
    score_put = 0

    reasons_call = []
    reasons_put = []

    # EMA trend
    if ema20 and ema50:
        if ema20 > ema50:
            score_call += 2
            reasons_call.append("EMA20 فوق EMA50")
        elif ema20 < ema50:
            score_put += 2
            reasons_put.append("EMA20 تحت EMA50")

    if ema200:
        if price > ema200:
            score_call += 1
            reasons_call.append("السعر فوق EMA200")
        elif price < ema200:
            score_put += 1
            reasons_put.append("السعر تحت EMA200")

    # RSI
    if current_rsi is not None:

        if 52 <= current_rsi <= 68:
            score_call += 1
            reasons_call.append("RSI يدعم الصعود")

        elif 32 <= current_rsi <= 48:
            score_put += 1
            reasons_put.append("RSI يدعم الهبوط")

    # MACD
    if macd_line is not None:

        if macd_line > 0:
            score_call += 1
            reasons_call.append("MACD موجب")

        elif macd_line < 0:
            score_put += 1
            reasons_put.append("MACD سالب")

    # Bollinger
    if upper and middle and lower:

        if price > middle:
            score_call += 1
            reasons_call.append("السعر فوق منتصف Bollinger")

        elif price < middle:
            score_put += 1
            reasons_put.append("السعر تحت منتصف Bollinger")

    # Support / resistance
    if support and resistance:

        distance_support = abs(price - support)
        distance_resistance = abs(resistance - price)

        if distance_support < distance_resistance:
            score_call += 1
            reasons_call.append("قرب دعم")

        elif distance_resistance < distance_support:
            score_put += 1
            reasons_put.append("قرب مقاومة")

    # Candle momentum
    last = candles[-1]

    body = last["close"] - last["open"]

    candle_range = last["high"] - last["low"]

    if candle_range > 0:

        body_ratio = abs(body) / candle_range

        if body > 0 and body_ratio >= 0.55:
            score_call += 1
            reasons_call.append("شمعة صاعدة قوية")

        elif body < 0 and body_ratio >= 0.55:
            score_put += 1
            reasons_put.append("شمعة هابطة قوية")

    # ATR must exist
    if current_atr is None:
        return {
            "direction": "WAIT",
            "score": 0,
            "confidence": 0,
            "reason": "ATR غير متوفر."
        }

    if score_call > score_put:
        direction = "CALL"
        score = score_call
        reasons = reasons_call

    elif score_put > score_call:
        direction = "PUT"
        score = score_put
        reasons = reasons_put

    else:
        direction = "WAIT"
        score = 0
        reasons = ["الإشارات متعادلة."]

    confidence = min(99, int((score / 10) * 100))

    return {
        "direction": direction,
        "score": score,
        "confidence": confidence,
        "rsi": current_rsi,
        "ema20": ema20,
        "ema50": ema50,
        "ema200": ema200,
        "atr": current_atr,
        "support": support,
        "resistance": resistance,
        "reasons": reasons,
    }


# =========================
# MULTI TIMEFRAME ANALYSIS
# =========================

TIMEFRAMES = {
    "1": {
        "name": "M1",
        "seconds": 60,
        "setup": 300,
        "trend": 900,
        "expiry": "1 دقيقة",
    },
    "5": {
        "name": "M5",
        "seconds": 300,
        "setup": 900,
        "trend": 1800,
        "expiry": "5 دقائق",
    },
    "15": {
        "name": "M15",
        "seconds": 900,
        "setup": 1800,
        "trend": 3600,
        "expiry": "15 دقيقة",
    },
    "30": {
        "name": "M30",
        "seconds": 1800,
        "setup": 3600,
        "trend": 3600,
        "expiry": "30 دقيقة",
    },
}


async def multi_timeframe_analysis(symbol, selected):
    tf = TIMEFRAMES[selected]

    entry_candles = await get_candles(
        symbol,
        tf["seconds"],
        300,
    )

    setup_candles = await get_candles(
        symbol,
        tf["setup"],
        200,
    )

    trend_candles = await get_candles(
        symbol,
        tf["trend"],
        200,
    )

    entry = analyze(entry_candles)
    setup = analyze(setup_candles)
    trend = analyze(trend_candles)

    return entry, setup, trend, tf


# =========================
# TELEGRAM UI
# =========================

def timeframe_keyboard(symbol):
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "1 دقيقة",
                callback_data=f"tf|{symbol}|1"
            )
        ],
        [
            InlineKeyboardButton(
                "5 دقائق",
                callback_data=f"tf|{symbol}|5"
            )
        ],
        [
            InlineKeyboardButton(
                "15 دقيقة",
                callback_data=f"tf|{symbol}|15"
            )
        ],
        [
            InlineKeyboardButton(
                "30 دقيقة",
                callback_data=f"tf|{symbol}|30"
            )
        ],
    ])


def symbol_keyboard(symbols, page=0):
    page_size = 12

    start = page * page_size
    items = symbols[start:start + page_size]

    rows = []

    for symbol in items:
        rows.append([
            InlineKeyboardButton(
                symbol,
                callback_data=f"sym|{symbol}"
            )
        ])

    navigation = []

    if page > 0:
        navigation.append(
            InlineKeyboardButton(
                "⬅️ السابق",
                callback_data=f"page|{page-1}"
            )
        )

    if start + page_size < len(symbols):
        navigation.append(
            InlineKeyboardButton(
                "التالي ➡️",
                callback_data=f"page|{page+1}"
            )
        )

    if navigation:
        rows.append(navigation)

    return InlineKeyboardMarkup(rows)


# =========================
# COMMANDS
# =========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "🤖 أهلاً بك في LiquidityArabicBot\n\n"
        "البوت جاهز لتحليل OTC.\n\n"
        "الأوامر:\n"
        "/otc — اختيار زوج OTC وتحليله\n"
        "/history — سجل الإشارات\n"
        "/stats — الإحصائيات\n"
        "/today — إشارات اليوم\n"
    )

    await update.message.reply_text(text)


async def otc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not OTC_API_KEY:
        await update.message.reply_text(
            "⚠️ البوت يعمل، لكن مفتاح بيانات OTC غير مضاف بعد.\n\n"
            "نضيفه في Render كـ OTCHARTS_API_KEY في الخطوة التالية."
        )
        return

    await update.message.reply_text(
        "⏳ جاري تحميل أزواج OTC المتاحة..."
    )

    try:
        symbols = await get_symbols()

        if not symbols:
            await update.message.reply_text(
                "لم تصل قائمة أزواج OTC من مزود البيانات."
            )
            return

        context.user_data["symbols"] = symbols

        await update.message.reply_text(
            f"📊 أزواج OTC المتاحة: {len(symbols)}\n\n"
            "اختر الزوج:",
            reply_markup=symbol_keyboard(symbols, 0),
        )

    except Exception as e:
        await update.message.reply_text(
            f"❌ تعذر تحميل أزواج OTC.\n\n{str(e)[:500]}"
        )


async def history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    con = sqlite3.connect(DB_PATH)

    rows = con.execute(
        """
        SELECT symbol, timeframe, direction, confidence, created_at
        FROM signals
        ORDER BY id DESC
        LIMIT 10
        """
    ).fetchall()

    con.close()

    if not rows:
        await update.message.reply_text(
            "لا توجد إشارات مسجلة حتى الآن."
        )
        return

    lines = ["📚 آخر الإشارات:\n"]

    for row in rows:
        symbol, tf, direction, confidence, created_at = row

        lines.append(
            f"{symbol} | {tf} | {direction} | {confidence}%"
        )

    await update.message.reply_text(
        "\n".join(lines)
    )


async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    con = sqlite3.connect(DB_PATH)

    total = con.execute(
        "SELECT COUNT(*) FROM signals"
    ).fetchone()[0]

    con.close()

    await update.message.reply_text(
        f"📊 إحصائيات البوت\n\n"
        f"إجمالي الإشارات: {total}"
    )


async def today(update: Update, context: ContextTypes.DEFAULT_TYPE):
    con = sqlite3.connect(DB_PATH)

    today_date = datetime.now(timezone.utc).date().isoformat()

    total = con.execute(
        """
        SELECT COUNT(*)
        FROM signals
        WHERE substr(created_at, 1, 10) = ?
        """,
        (today_date,),
    ).fetchone()[0]

    con.close()

    await update.message.reply_text(
        f"📅 إشارات اليوم: {total}"
    )


# =========================
# CALLBACKS
# =========================

async def callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query

    await query.answer()

    data = query.data

    # symbol selected
    if data.startswith("sym|"):
        symbol = data.split("|", 1)[1]

        await query.edit_message_text(
            f"💱 الزوج: {symbol}\n\n"
            "اختر الفريم:",
            reply_markup=timeframe_keyboard(symbol),
        )

        return

    # page navigation
    if data.startswith("page|"):
        page = int(data.split("|", 1)[1])

        symbols = context.user_data.get("symbols", [])

        if not symbols:
            await query.edit_message_text(
                "انتهت الجلسة. استخدم /otc مرة أخرى."
            )
            return

        await query.edit_message_text(
            f"📊 أزواج OTC — الصفحة {page + 1}\n\n"
            "اختر الزوج:",
            reply_markup=symbol_keyboard(symbols, page),
        )

        return

    # timeframe selected
    if data.startswith("tf|"):
        _, symbol, selected = data.split("|", 2)

        tf = TIMEFRAMES.get(selected)

        if not tf:
            await query.edit_message_text(
                "فريم غير صالح."
            )
            return

        await query.edit_message_text(
            f"🔎 جاري تحليل {symbol}\n"
            f"الفريم: {tf['name']}\n\n"
            "جاري فحص الاتجاه العام + الإعداد + الدخول..."
        )

        try:
            entry, setup, trend, tf = await multi_timeframe_analysis(
                symbol,
                selected,
            )

            # Multi-timeframe agreement
            direction = entry["direction"]

            agreement = 0

            if direction != "WAIT":
                if setup["direction"] == direction:
                    agreement += 1

                if trend["direction"] == direction:
                    agreement += 1

            final_score = entry["score"] + agreement * 2

            # Require confirmation from at least entry + one higher TF
            confirmed = (
                direction in ("CALL", "PUT")
                and final_score >= SIGNAL_SCORE
                and agreement >= 1
            )

            if not confirmed:
                await query.edit_message_text(
                    f"⚠️ لا توجد إشارة مؤكدة الآن\n\n"
                    f"💱 {symbol}\n"
                    f"⏱ {tf['name']}\n\n"
                    f"الدخول: {entry['direction']}\n"
                    f"الإعداد: {setup['direction']}\n"
                    f"الاتجاه العام: {trend['direction']}\n\n"
                    f"النقاط: {final_score}\n\n"
                    "تم رفض الإشارة لأن التأكيدات غير كافية."
                )
                return

            confidence = min(
                99,
                int((final_score / 12) * 100)
            )

            save_signal(
                symbol,
                tf["name"],
                direction,
                confidence,
                final_score,
            )

            reasons = entry.get("reasons", [])

            reason_text = "\n".join(
                f"• {r}" for r in reasons[:6]
            )

            message = (
                "🟢 إشارة OTC مؤكدة\n\n"
                f"💱 الزوج: {symbol}\n"
                f"📈 الاتجاه: {direction}\n"
                f"⏱ الفريم: {tf['name']}\n"
                f"⌛ المدة المقترحة: {tf['expiry']}\n"
                f"🔥 قوة الإعداد: {confidence}%\n"
                f"📊 النقا
