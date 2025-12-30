# استخدم Python 3.11 الرسمي
FROM python:3.11-slim

# تعيين مجلد العمل داخل الحاوية
WORKDIR /app

# نسخ ملفات المشروع (bot.py و requirements.txt)
COPY requirements.txt .
COPY bot.py .

# تثبيت المكتبات المطلوبة
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# تحديد متغير البيئة للـ Telegram Bot Token
# على Railway يمكنك إضافته من Dashboard بدل كتابته هنا
# ENV BOT_TOKEN=YOUR_BOT_TOKEN_HERE

# أمر تشغيل البوت
CMD ["python", "bot.py"]
