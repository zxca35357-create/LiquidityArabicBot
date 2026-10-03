استيراد نظام التشغيل
استيراد sqlite3
استيراد asyncio
استيراد الرياضيات
من datetime استورد datetime و timezone

استيراد aiohttp
من تيليجرام استورد التحديث، زر لوحة المفاتيح المضمنة، ترميز لوحة المفاتيح المضمنة
من مكتبة telegram.ext استورد (
    طلب،
    معالج الأوامر،
    معالج استعلام رد الاتصال،
    أنواع السياق،
)

# =========================
# إعدادات
# =========================

DB_PATH = os.getenv("DB_PATH", "bot.db")
PORT = int(os.getenv("PORT", "10000"))
WEBHOOK_PATH = os.getenv("WEBHOOK_PATH", "/telegram")

OTC_API_KEY = os.getenv("OTCHARTS_API_KEY", "")
OTC_BASE_URL = os.getenv("OTCHARTS_BASE_URL", "https://otcharts.com")

VENUE = os.getenv("OTC_VENUE", "otc")

# الحد الأدنى للدرجة المطلوبة للإشارة
SIGNAL_SCORE = int(os.getenv("SIGNAL_SCORE", "8"))

# =========================
قاعدة بيانات جديدة
# =========================

def init_db():
    con = sqlite3.connect(DB_PATH)

    con.execute("""
        إنشاء جدول الإشارات إذا لم يكن موجودًا (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            الرمز TEXT NOT NULL،
            timeframe TEXT NOT NULL,
            الاتجاه نص غير فارغ،
            الثقة عدد صحيح غير فارغ،
            النتيجة عدد صحيح غير فارغ
        )
    """)

    con.commit()
    con.close()


دالة حفظ_الإشارة(الرمز، الإطار الزمني، الاتجاه، الثقة، النتيجة):
    con = sqlite3.connect(DB_PATH)

    con.execute(
        """
        INSERT INTO signals
        (تاريخ الإنشاء، الرمز، الإطار الزمني، الاتجاه، الثقة، النتيجة)
        قيم (؟، ؟، ؟، ؟، ؟، ؟)
        "",
        (
            datetime.now(timezone.utc).isoformat(),
            رمز،
            الإطار الزمني،
            اتجاه،
            ثقة،
            نتيجة،
        )
    )

    con.commit()
    con.close()


# =========================
واجهة برمجة تطبيقات OTC المحلية
# =========================

async def api_get(path, params=None):
    إذا لم يكن OTC_API_KEY:
        ارفع خطأ وقت التشغيل (
            "OTCHARTS_API_KEY ط؛ظٹط± ظ…ظˆط¬ظˆط¯ ظپظٹ متغيرات البيئة."
        )

    الرؤوس = {
        "التفويض": f"حامل {OTC_API_KEY}",
        "قبول": "application/json",
    }

    url = OTC_BASE_URL.rstrip("/") + path

    timeout = aiohttp.ClientTimeout(total=20)

    async with aiohttp.ClientSession(timeout=timeout) as session:
        async with session.get(
            عنوان URL،
            headers=headers,
            params=params or {},
        ) كرد فعل:

            text = await response.text()

            إذا كانت حالة الاستجابة لا تساوي 200:
                ارفع خطأ وقت التشغيل (
                    f"OTC API HTTP {response.status}: {text[:300]}"
                )

            يحاول:
                استيراد json
                return json.loads(text)
            باستثناء الاستثناء:
                rise RuntimeError("OTC API ط±ط¬ط¹ ط¨ظٹط§ظ†ط§طھ ط؛ظٹط± طμط§ظ„طط©.")


async def get_symbols():
    data = await api_get("/v1/symbols")

    # عادةً ما تتضمن استجابة OTCharts الحالية أماكن.
    venues = data.get("venues", [])

    للمكان في الأماكن:
        إذا كان `venue.get("id") == VENUE:`
            instruments = venue.get("instruments")

            إذا كانت الأدوات:
                النتيجة = []

                بالنسبة للعنصر الموجود في الأدوات:
                    إذا كان العنصر من نوع سلسلة نصية:
                        result.append(item)
                    elif isinstance(item, dict):
                        symbol = item.get("symbol")
                        إذا كان الرمز:
                            result.append(symbol)

                إرجاع النتيجة

    # قد تعرض بعض استجابات واجهة برمجة التطبيقات الرموز بشكل مختلف.
    symbols = data.get("symbols", [])

    النتيجة = []

    for item in symbols:
        إذا كان العنصر من نوع سلسلة نصية:
            result.append(item)
        elif isinstance(item, dict):
            symbol = item.get("symbol")
            إذا كان الرمز:
                result.append(symbol)

    إرجاع النتيجة


async def get_candles(symbol, timeframe_seconds, limit=300):
    البيانات = انتظر api_get(
        "/v1/candles",
        {
            "المكان": المكان،
            "رمز": رمز،
            "tf": timeframe_seconds,
            "الحد": الحد،
        },
    )

    candles = data.get("candles", [])

    تم التنظيف = []

    for c in candles:
        يحاول:
            تم تنظيفها.أضف({
                "open": float(c["open"]),
                "عالي": float(c["عالي"]),
                "منخفض": float(c["منخفض"]),
                "إغلاق". float(c["إغلاق"]),
                "الوقت": int(c["الوقت"]),
                "الحجم": float(c.get("الحجم", 0)),
            })
        باستثناء الاستثناء:
            يكمل

    تم تنظيفها عند العودة


# =========================
المؤشرات الفنية
# =========================

def ema(values, period):
    إذا كان طول (القيم) أقل من الفترة:
        لا شيء

    المضاعف = 2 / (الدورة + 1)

    التيار = مجموع (القيم[:الفترة]) / الفترة

    for price in values[period:]:
        الحالي = (
            (السعر - السعر الحالي) * المضاعف
        ) + التيار

    إرجاع الحالي


def rsi(values, period=14):
    إذا كان طول (القيم) < الفترة + 1:
        لا شيء

    المكاسب = []
    الخسائر = []

    for i in range(1, len(values)):
        التغيير = القيم[i] - القيم[i - 1]

        gains.append(max(change, 0))
        loss.append(max(-change, 0))

    متوسط ​​الربح = مجموع(الربح[:الفترة]) / الفترة
    متوسط_الخسارة = مجموع(الخسائر[:الفترة]) / الفترة

    for i in range(period, len(gains)):
        متوسط ​​الربح = ((متوسط ​​الربح * (الفترة - 1)) + المكاسب[i]) / الفترة
        متوسط_الخسارة = ((متوسط_الخسارة * (الفترة - 1)) + الخسائر[i]) / الفترة

    إذا كان متوسط ​​الخسارة يساوي صفرًا:
        إرجاع 100.0

    rs = متوسط ​​الربح / متوسط ​​الخسارة

    أعد 100 - (100 / (1 + rs))


دالة macd(القيم):
    إذا كان طول (القيم) أقل من 35:
        إرجاع لا شيء، لا شيء

    fast = ema(values, 12)
    slow = ema(values, 26)

    إذا كانت قيمة "سريع" أو "بطيء" هي "لا شيء":
        إرجاع لا شيء، لا شيء

    # تقريب خط MACD من أحدث قيم EMA.
    خط ماكد = سريع - بطيء

    أرجع macd_line، لا شيء


دالة بولينجر (القيم، الفترة = 20، الانحراف = 2):
    إذا كان طول (القيم) أقل من الفترة:
        إرجاع لا شيء، لا شيء، لا شيء

    القيم الحديثة = القيم[-الفترة:]

    الوسط = مجموع (الأحدث) / الفترة

    التباين = مجموع (
        (س - الوسط) ** 2
        لكل x في الآونة الأخيرة
    ) / فترة

    الانحراف المعياري = الجذر التربيعي للتباين

    الحد الأعلى = الوسط + الانحراف المعياري * الانحراف المعياري
    الحد الأدنى = المتوسط ​​- الانحراف المعياري * الانحراف المعياري

    العودة إلى الأعلى، والوسط، والأسفل


دالة atr(الشموع، الفترة=14):
    إذا كان عدد الشموع أقل من الفترة + 1:
        لا شيء

    trs = []

    for i in range(1, len(candles)):
        الحالي = الشموع[i]
        previous = candles[i - 1]

        tr = max(
            current["high"] - current["low"],
            القيمة المطلقة (القيمة الحالية["الأعلى"] - القيمة السابقة["الإغلاق"])،
            القيمة المطلقة (القيمة الحالية["الأدنى"] - القيمة السابقة["الإغلاق"])،
        )

        trs.append(tr)

    إذا كان طول (trs) أقل من الفترة:
        لا شيء

    أرجع مجموع (trs[-period:]) / الفترة


def support_resistance(candles, lookback=40):
    إذا كان عدد الشموع أقل من 10:
        إرجاع لا شيء، لا شيء

    recent = candles[-lookback:]

    الدعم = الحد الأدنى(ج["منخفض"] لكل ج في الأحدث)
    المقاومة = الحد الأقصى (ج["عالي"] لكل ج في الأخيرة)

    دعم العودة، مقاومة


# =========================
# تحليل
# =========================

def analyze(candles):
    إذا كان عدد الشموع أقل من 80:
        يعود {
            "الاتجاه": "انتظر"،
            النتيجة: 0
            "الثقة": 0،
            "reason": "ط¹ط¯ط¯ ط§ظ„ط´ظ…ظˆط¹ ط؛ظٹط± ظƒط§ظپظچ ظظ„طھطظ„ظٹظ„."
        }

    closes = [c["close"] for c in candles]

    السعر = إغلاق[-1]

    ema20 = ema(closes, 20)
    ema50 = ema(closes, 50)
    ema200 = ema(closes, 200)

    current_rsi = rsi(closes, 14)

    macd_line, _ = macd(closes)

    أعلى، وسط، أسفل = مؤشر بولينجر (أسعار الإغلاق)

    current_atr = atr(candles, 14)

    الدعم، المقاومة = دعم_المقاومة(الشموع)

    score_call = 0
    score_put = 0

    سبب_الاستدعاء = []
    reasons_put = []

    اتجاه المتوسط ​​المتحرك الأسي
    إذا كان متوسط ​​الخطأ التربيعي المتوسط ​​20 ومتوسط ​​الخطأ التربيعي المتوسط ​​50:
        إذا كان متوسط ​​الخطأ الموسع 20 أكبر من متوسط ​​الخطأ الموسع 50:
            score_call += 2
            reasons_call.append("EMA20 ظپظˆظ‚ EMA50")
        elif ema20 < ema50:
            score_put += 2
            reasons_put.append("EMA20 طھططھ EMA50")

    إذا كان ema200:
        إذا كان السعر > المتوسط ​​المتحرك الأسي 200:
            score_call += 1
            Reasons_call.append("ط§ظ„ط³ط¹ط± ظپظˆظ‚ EMA200")
        elif price < ema200:
            score_put += 1
            Reasons_put.append("ط§ظ„ط³ط¹ط± طھططھ EMA200")

    مؤشر القوة النسبية
    إذا لم تكن قيمة current_rsi تساوي None:

        إذا كان 52 <= current_rsi <= 68:
            score_call += 1
            reason_call.append("RSI ظٹط¯ط¹ظ… ط§ظ„طµط¹ظˆط¯")

        elif 32 <= current_rsi <= 48:
            score_put += 1
            reasons_put.append("RSI ظٹط¯ط¹ظ… ط§ظ„ظ‡ط¨ظˆط·")

    ماكد
    إذا لم يكن macd_line يساوي None:

        إذا كان خط ماكد أكبر من 0:
            score_call += 1
            reasons_call.append("MACD ظ…ظˆط¬ط¨")

        elif macd_line < 0:
            score_put += 1
            reasons_put.append("MACD ط³ط§ظ„ط¨")

    دي بولينجر
    إذا كان العلوي والأوسط والسفلي:

        إذا كان السعر أكبر من السعر المتوسط:
            score_call += 1
            Reasons_call.append("ط§ظ"ط³ط¹ط± ظپظˆظ‚ ظ…ظ†طھطμظپ بولينجر")

        elif price < middle:
            score_put += 1
            Reasons_put.append("ط§ظ"ط³ط¹ط± طھططھ ظ…ظ†طھطμظپ بولينجر")

    الدعم / المقاومة
    في حالة الدعم والمقاومة:

        دعم_المسافة = القيمة المطلقة (السعر - الدعم)
        المقاومة_المسافة = القيمة المطلقة(المقاومة - السعر)

        إذا كانت مسافة الدعم < مسافة المقاومة:
            score_call += 1
            reasons_call.append("ظ‚ط±ط¨ ط¯ط¹ظ…")

        elif distance_resistance < distance_support:
            score_put += 1
            Reasons_put.append("ظ‚ط±ط¨ ظ…ظ‚ط§ظˆظ…ط©”)

    زخم الشموع
    last = candles[-1]

    body = last["close"] - last["open"]

    نطاق_الشموع = آخر["أعلى"] - آخر["أدنى"]

    إذا كان نطاق الشمعة > 0:

        نسبة_الجسم = القيمة_القيمة ...

        إذا كان حجم الجسم > 0 ونسبة الجسم >= 0.55:
            score_call += 1
            Reasons_call.append("ط´ظ…ط¹ط© ط¹ط§ط¹ط¯ط© ظ‚ظˆظٹط©”

        elif body < 0 and body_ratio >= 0.55:
            score_put += 1
            Reasons_put.append("ط´ظ…ط¹ط© ظ‡ط§ط¨ط·ط© ظ‚ظˆظٹط©")

    يجب أن يكون ATR موجودًا
    إذا كانت قيمة current_atr تساوي None:
        يعود {
            "الاتجاه": "انتظر"،
            النتيجة: 0
            "الثقة": 0،
            "reason": "ATR ط؛ظٹط± ظ…طھظˆظپط±."
        }

    إذا كانت قيمة الاستدعاء أكبر من قيمة الإخراج:
        الاتجاه = "اتصال"
        النتيجة = استدعاء_النتيجة
        الأسباب = استدعاء_الأسباب

    elif score_put > score_call:
        الاتجاه = "وضع"
        النتيجة = النتيجة_المُدخلة
        الأسباب = وضع_الأسباب

    آخر:
        الاتجاه = "انتظر"
        النتيجة = 0
        الأسباب = ["ط§ظ"ط¥ط´ط§ط±ط§طھ ظ…طھط¹ط§ط¯ظ"ط©."]

    الثقة = الحد الأدنى (99، العدد الصحيح ((النتيجة / 10) * 100))

    يعود {
        "الاتجاه": الاتجاه،
        "النتيجة": النتيجة،
        "الثقة": الثقة،
        "rsi": current_rsi,
        "ema20": ema20,
        "ema50": ema50,
        "ema200": ema200,
        "atr": current_atr,
        "الدعم": الدعم،
        "المقاومة": المقاومة،
        "الأسباب": الأسباب،
    }


# =========================
# تحليل متعدد الأطر الزمنية
# =========================

الأطر الزمنية = {
    "1": {
        "الاسم": "M1"،
        "ثوانٍ": 60،
        الإعداد: 300
        "الاتجاه": 900،
        "expiry": "1 ط¯ظ‚ظٹظ‚ط©",
    },
    "5": {
        "الاسم": "M5"،
        "ثوانٍ": 300،
        الإعداد: 900
        "الاتجاه": 1800،
        "تاريخ الانتهاء": "5 ط¯ظ‚ط§ط¦ظ‚",
    },
    "15": {
        "الاسم": "M15"
        "ثوانٍ": 900،
        "الإعداد": 1800،
        "الاتجاه": 3600،
        "expiry": "15 ط¯ظ‚ظٹظ‚ط©",
    },
    "30": {
        "الاسم": "M30"
        "ثوانٍ": 1800،
        الإعداد: 3600،
        "الاتجاه": 3600،
        "expiry": "30 ط¯ظ‚ظٹظ‚ط©",
    },
}


async def multi_timeframe_analysis(symbol, selected):
    tf = TIMEFRAMES[selected]

    entry_candles = await get_candles(
        رمز،
        tf["seconds"],
        300،
    )

    setup_candles = await get_candles(
        رمز،
        tf["setup"],
        200،
    )

    trend_candles = await get_candles(
        رمز،
        tf["trend"],
        200،
    )

    entry = analyze(entry_candles)
    الإعداد = تحليل(إعداد_الشموع)
    trend = analyze(trend_candles)

    إرجاع الدخول، الإعداد، الاتجاه، الإطار الزمني


# =========================
# واجهة مستخدم تيليجرام
# =========================

دالة لوحة المفاتيح الخاصة بالإطار الزمني (الرمز):
    إرجاع InlineKeyboardMark([
        [
            زر لوحة المفاتيح المضمن (
                "1 ط¯ظ‚ظٹظ‚ط©",
                callback_data=f"tf|{symbol}|1"
            )
        ],
        [
            زر لوحة المفاتيح المضمن (
                "5 ط¯ظ‚ط§ط¦ظ‚",
                callback_data=f"tf|{symbol}|5"
            )
        ],
        [
            زر لوحة المفاتيح المضمن (
                "15 ط¯ظ‚ظٹظ‚ط©",
                callback_data=f"tf|{symbol}|15"
            )
        ],
        [
            زر لوحة المفاتيح المضمن (
                "30 ط¯ظ‚ظٹظ‚ط©",
                callback_data=f"tf|{symbol}|30"
            )
        ],
    ])


دالة symbol_keyboard(symbols, page=0):
    حجم_الصفحة = 12

    بداية = الصفحة * حجم_الصفحة
    العناصر = الرموز[البداية:البداية + حجم_الصفحة]

    صفوف = []

    لكل رمز في العناصر:
        rows.append([
            زر لوحة المفاتيح المضمن (
                رمز،
                callback_data=f"sym|{symbol}"
            )
        ])

    التنقل = []

    إذا كانت الصفحة > 0:
        navigation.append(
            زر لوحة المفاتيح المضمن (
                "â¬…ï¸ڈ ط§ظ„ط³ط§ط¨ظ‚“,
                callback_ata=f"page|{page-1}"
            )
        )

    إذا كان مجموع قيمة البداية وحجم الصفحة أقل من طول الرموز:
        navigation.append(
            زر لوحة المفاتيح المضمن (
                "ط§ظ"طھط§ظ"ظٹ ‍،ï¸ڈ"،
                callback_ata=f"page|{page+1}"
            )
        )

    في حالة التنقل:
        rows.append(navigation)

    return InlineKeyboardMarkup(rows)


# =========================
الأوامر
# =========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    النص = (
        "ًں¤– ط £ظ‡ظ„ط§ظ‹ ط¨ظƒ ظپظٹ LiquidityArabicBot\n\n"
        "ط§ظ"ط¨ظˆطھ ط¬ط§ظ‡ط² ظ"طھطظ"ظٹظ" OTC.\n\n"
        "ط§ظ"ط £ظˆط§ظ…ط±:\n"
        "/otc – ط§ط®طھظٹط§ط± ط²ظˆط¬ OTC ظˆطھطظ„ظٹظ„ظ‡\n"
        "/history — ط³ط¬ظ„ ط§ظ„ط¥ط´ط§ط±ط§طھ\n”
        "/stats — ط§ظ„ط¥ططµط§ط¦ظٹط§طھ\n"
        "/ اليوم – ط¥ط´ط§ط±ط§طھ ط§ظ„ظٹظˆظ…\n"
    )

    await update.message.reply_text(text)


async def otc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    إذا لم يكن OTC_API_KEY:
        انتظر تحديث.الرسالة.نص الرد(
            "âڑ ï¸ڈ ط§ظ„ط¨ظˆطھ ظٹط¹ظ…ظ„طŒ ظ„ظƒظ† ظ…ظپطھط§ط ط¨ظٹط§ظ†ط§طھ OTC ط؛ظٹط± ظ…ط¶ط§ظپ ط¨ط¹ط¯.\n\n"
            "ظ†ط¶ظٹظپظ‡ ظپظٹ Render ظƒظ€ OTCHARTS_API_KEY ظپظٹ ط§ظ„ط®ط·ظˆط© ط§ظ„طھط§ظ„ظٹط©.”
        )
        يعود

    انتظر تحديث.الرسالة.نص الرد(
        "âڈ³ ط¬ط§ط±ظٹ طھطظ…ظٹظ„ ط £ط²ظˆط§ط¬ OTC ط§ظ„ظ…طھط§ط©..."
    )

    يحاول:
        الرموز = انتظر الحصول على الرموز()

        إذا لم تكن رموزًا:
            انتظر تحديث.الرسالة.نص الرد(
                "ظ"ظ… طھطμظ„ ظ‚ط§ط¦ظ…ط© ط £ط²ظˆط§ط¬ OTC ظ…ظ† ظ…ط²ظˆط¯ ط§ظ„ط¨ظٹط§ظ†ط§طھ.”
            )
            يعود

        context.user_data["symbols"] = symbols

        انتظر تحديث.الرسالة.نص الرد(
            f"ًں“ٹ ط £ط²ظˆط§ط¬ OTC ط§ظ„ظ…طھط§طط©: {len(symbols)}\n\n"
            "ط§ط®طھط± ط§ظ"ط²ظˆط¬:,
            reply_markup=symbol_keyboard(symbols, 0),
        )

    باستثناء الاستثناء كـ e:
        انتظر تحديث.الرسالة.نص الرد(
            f"â‌Œ طھط¹ط°ط± طھطظ…ظٹظ„ ط £ط²ظˆط§ط¬ OTC.\n\n{str(e)[:500]}"
        )


async def history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    con = sqlite3.connect(DB_PATH)

    rows = con.execute(
        """
        حدد الرمز، والإطار الزمني، والاتجاه، ومستوى الثقة، وتاريخ الإنشاء
        من الإشارات
        ترتيب حسب المعرف تنازليًا
        الحد الأقصى 10
        """
    ).fetchall()

    con.close()

    إذا لم تكن هناك صفوف:
        انتظر تحديث.الرسالة.نص الرد(
            "ظ"ط§ طھظˆط¬ط¯ ط¥ط´ط§ط±ط§طھ ظ…ط³ط¬ظ„ط© ططھظ‰ ط§ظ„ط ™ظ†.”
        )
        يعود

    lines = ["ں“ڑ ط¢ط®ط± ط§ظ„ط¥ط´ط§ط±ط§طھ:\n”]

    for row in rows:
        الرمز، tf، الاتجاه، الثقة، تاريخ الإنشاء = الصف

        lines.append(
            f"{symbol} | {tf} | {direction} | {confidence}%"
        )

    انتظر تحديث.الرسالة.نص الرد(
        "\n".join(lines)
    )


async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    con = sqlite3.connect(DB_PATH)

    المجموع = con.execute(
        "SELECT COUNT(*) FROM signals"
    ).fetchone()[0]

    con.close()

    انتظر تحديث.الرسالة.نص الرد(
        f"ًں“ٹ ط¥ططμط§ط¦ظٹط§طھ ط§ظ„ط¨ظˆطھ\n\n”
        f"ط¥ط¬ظ…ط§ظ„ظٹ ط§ظ„ط¥ط´ط§ط±ط§طھ: {total}"
    )


async def today(update: Update, context: ContextTypes.DEFAULT_TYPE):
    con = sqlite3.connect(DB_PATH)

    تاريخ_اليوم = datetime.now(timezone.utc).date().isoformat()

    المجموع = con.execute(
        """
        حدد عدد السجلات (*)
        من الإشارات
        حيث يكون الجزء الفرعي (created_at، 1، 10) = ؟
        "",
        (تاريخ_اليوم،)،
    ).fetchone()[0]

    con.close()

    انتظر تحديث.الرسالة.نص الرد(
        f"ًں“… ط¥ط´ط§ط±ط§طھ ط§ظ„ظٹظˆظ…: {total}"
    )


# =========================
# معاودة الاتصال
# =========================

async def callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    الاستعلام = update.callback_query

    await query.answer()

    البيانات = استعلام.البيانات

    تم تحديد الرمز الفرعي
    إذا كانت البيانات تبدأ بـ "sym|":
        symbol = data.split("|", 1)[1]

        await query.edit_message_text(
            f"ًں'± ط§ظط²ظˆط¬: {الرمز}\n\n"
            "ط§ط®طھط± ط§ظ„ظپط±ظٹظ…:",
            reply_markup=timeframe_keyboard(symbol),
        )

        يعود

    التنقل بين الصفحات
    إذا كانت البيانات تبدأ بـ "page|":
        page = int(data.split("|", 1)[1])

        symbols = context.user_data.get("symbols", [])

        إذا لم تكن رموزًا:
            await query.edit_message_text(
                "ط§ظ†طھظ‡طھ ط§ظ"ط¬ظ"ط³ط©.ط§ط³طھط®ط¯ظ… /otc ظ…ط±ط© ط £ط®ط±ظ‰."
            )
            يعود

        await query.edit_message_text(
            f"ًں“ٹ ط £ط²ظˆط§ط¬ OTC â€” ط§ظ„طμظپطط© {page + 1}\n\n"
            "ط§ط®طھط± ط§ظ"ط²ظˆط¬:,
            reply_markup=symbol_keyboard(symbols, page),
        )

        يعود

    تم اختيار الإطار الزمني
    إذا كانت البيانات تبدأ بـ "tf|":
        _, symbol, selected = data.split("|", 2)

        tf = TIMEFRAMES.get(selected)

        وإلا:
            await query.edit_message_text(
                "ظپط±ظٹظ… ط؛ظٹط± طμط§ظ„ط."
            )
            يعود

        await query.edit_message_text(
            f"ًں"ژ ط¬ط§ط±ظٹ طھطظ‹ظٹظ‹ {رمز}\n"
            f"ط§ظ„ظپط±ظٹظ…: {tf['name']}\n\n"
            "ط¬ط§ط±ظٹ ظپططμ ط§ظ‹ط§طھط¬ط§ظ‡ ط§ظ‹ط¹ط§ظ… + ط§ظ‹ط¥ط¹ط¯ط§ط¯ + ط§ظ‹ط¯ط®ظˆظ‹...”
        )

        يحاول:
            الدخول، الإعداد، الاتجاه، الإطار الزمني = انتظر تحليل الإطار الزمني المتعدد(
                رمز،
                تم الاختيار،
            )

            # اتفاقية متعددة الأطر الزمنية
            الاتجاه = المدخل["الاتجاه"]

            الاتفاق = 0

            إذا كان الاتجاه لا يساوي "انتظر":
                إذا كان الإعداد["الاتجاه"] يساوي الاتجاه:
                    الاتفاق += 1

                إذا كان اتجاه الاتجاه يساوي الاتجاه:
                    الاتفاق += 1

            النتيجة النهائية = المدخل["النتيجة"] + الاتفاق * 2

            # يتطلب تأكيدًا من جهة إدخال واحدة على الأقل + عامل أعلى
            تم التأكيد = (
                الاتجاه في ("CALL", "PUT")
                و final_score >= SIGNAL_SCORE
                والاتفاق ≥ 1
            )

            في حال عدم التأكيد:
                await query.edit_message_text(
                    f"âڑ ï¸ڈ ظ„ط§ طھظˆط¬ط¯ ط¥ط´ط§ط±ط© ظ…ط¤ظƒط¯ط© ط§ظ„طˆظ†\n\n"
                    f"ًں'± {رمز}\n"
                    f"âڈ± {tf['name']}\n\n"
                    f"ط§ظ„ط¯ط®ظˆظ„: {entry['direction']}\n"
                    f"ط§ظ„ط¥ط¹ط¯ط§ط¯: {setup['direction']}\n"
                    f"ط§ظ„ط§طھط¬ط§ظ‡ ط§ظ„ط¹ط§ظ…: {trend['direction']}\n\n"
                    f"ط§ظ„ظ†ظ‚ط§ط·: {النتيجة النهائية}\n\n"
                    "طھظ… ط±ظپط¶ ط§ظ‹ط¥ط´ط§ط±ط© ظ‹ط§ظ† ط§ظ‹طھط £ظƒظٹط¯ط§طھ ط؛ظٹط± ظƒط§ظپظٹط©.”
                )
                يعود

            الثقة = الحد الأدنى (
                99،
                int((final_score / 12) * 100)
            )

            حفظ_الإشارة(
                رمز،
                tf["name"],
                اتجاه،
                ثقة،
                النتيجة النهائية،
            )

            reasons = entry.get("reasons", [])

            reason_text = "\n".join(
                f"• {r}" for r in reason[:6]
            )

            الرسائل = (
                "ًںں ™ ط¥ط´ط§ط±ط© OTC ظ…ط¤ظƒط¯ط©\n\n"
                f"ًں'± ط§ظ„ط²ظˆط¬: {رمز}\n"
                f"ًں“ˆ ط§ظ„ط§طھط¬ط§ظ‡: {الاتجاه}\n"
                f"âڈ± ط§ظ„ظپط±ظٹظ…: {tf['name']}\n"
                f"âŒ› ط§ظ„ظ…ط¯ط© ط§ظ„ظ…ظ‚طھط±ط©: {tf['expiry']}\n"
                f"ًں"¥ ظ‚ظˆط© ط§ظ„ط¥ط¹ط¯ط§ط¯: {الثقة}%\n"
                f"ًں“ٹ ط§ظ„ظ†ظ‚ط§ط·: {final_score}\n\n"
                "طپط³ط¨ط§ط¨ ط§ظ"طھطظ"ظٹظ":\n"
                f"{reason_text}"
            )

            await query.edit_message_text(message)

        باستثناء الاستثناء كـ e:
            await query.edit_message_text(
                "â‌Œ طط¯ط« ط®ط·ط £ ط £ط«ظ†ط§ط، ط§ظ‹طھطظ‹ظٹظ„.\n\n"
                f"{str(e)[:500]}"
            )


# =========================
# طلب
# =========================

def main():
    token = os.getenv("BOT_TOKEN")

    إذا لم يكن رمزًا مميزًا:
        ارفع خطأ وقت التشغيل (
            "BOT_TOKEN ط؛ظٹط± ظ…ظˆط¬ظˆط¯ ظپظٹ متغيرات البيئة."
        )

    init_db()

    app = Application.builder().token(token).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("otc", otc))
    app.add_handler(CommandHandler("history", history))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CommandHandler("today", today))
    app.add_handler(CallbackQueryHandler(callback))

    external_url = os.getenv("RENDER_EXTERNAL_URL")

    إذا لم يكن عنوان URL الخارجي:
        ارفع خطأ وقت التشغيل (
            "RENDER_EXTERNAL_URL ط؛ظٹط± ظ…ظˆط¬ظˆط¯. ط´ط؛ظ'ظ„ ط§ظ„ط®ط¯ظ…ط© ظƒظ€ تقديم خدمة الويب."
        )

    webhook_url = (
        f"{external_url.rstrip('/')}/"
        f"{WEBHOOK_PATH.lstrip('/')}"
    )

    app.run_webhook(
        listen="0.0.0.0",
        المنفذ=PORT,
        url_path=WEBHOOK_PATH.lstrip("/"),
        webhook_url=webhook_url,
        drop_pending_updates=True,
    )


إذا كان __name__ == "__main__":
    رئيسي()
