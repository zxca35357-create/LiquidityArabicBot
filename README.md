# LiquidityArabicBot — Render Free Web Service

هذه النسخة معدلة لتعمل كـ Telegram webhook على Render Web Service المجاني بدل Background Worker المدفوع.

## إعداد Render

- Service type: Web Service
- Build Command: `pip install -r requirements.txt`
- Start Command: `python bot.py`
- Plan: Free
- Environment Variable:
  - Key: `BOT_TOKEN`
  - Value: توكن البوت من BotFather

Render يوفّر تلقائياً `RENDER_EXTERNAL_URL` للبوت، ويُستخدم لتسجيل Telegram webhook.

> ملاحظة: خطة Render المجانية قد تدخل الخدمة في وضع السكون بعد فترة من عدم وجود طلبات. قد يؤدي ذلك إلى تأخر بسيط عند أول رسالة بعد السكون.
