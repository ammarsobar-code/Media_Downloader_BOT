import os
import telebot
import yt_dlp
import time
import requests
import math # لإضافة عمليات حسابية
from threading import Thread
from flask import Flask
from fake_useragent import UserAgent
from telebot.types import InputMediaPhoto, InlineKeyboardMarkup, InlineKeyboardButton

# --- 1. إعدادات السيرفر والبوت ---
app = Flask('')
ua = UserAgent()

@app.route('/')
def home():
    return "Bot is running on Oracle Cloud!"

# دالة لرفع استهلاك المعالج قليلاً لتجنب إغلاق أوراكل للخمول
def cpu_stress():
    while True:
        # عملية حسابية بسيطة تتكرر كل فترة لضمان وجود نشاط
        for i in range(10**6):
            _ = math.sqrt(i)
        time.sleep(30) # ارتاح 30 ثانية ثم كرر

def run():
    # أوراكل لا تستخدم PORT متغير مثل ريلواي عادة، سنثبته على 8080
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    # تشغيل السيرفر
    t1 = Thread(target=run)
    t1.daemon = True
    t1.start()
    # تشغيل سكربت النشاط
    t2 = Thread(target=cpu_stress)
    t2.daemon = True
    t2.start()

# --- باقي الكود الخاص بمحركات التحميل والتحقق كما هو دون تغيير ---
# (انسخ دوال handle_tiktok و handle_snap_or_fallback هنا)
