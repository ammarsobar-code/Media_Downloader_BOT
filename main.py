import os
import telebot
import yt_dlp
import time
import requests
import math
from threading import Thread
from flask import Flask
from fake_useragent import UserAgent
from telebot.types import InputMediaPhoto, InlineKeyboardMarkup, InlineKeyboardButton
from dotenv import load_dotenv

# تحميل المتغيرات البيئية من ملف .env
load_dotenv()

# --- 1. إعدادات السيرفر والبوت ---
app = Flask('')
ua = UserAgent()

@app.route('/')
def home():
    return "Bot is running on Oracle Cloud!"

# دالة لرفع استهلاك المعالج قليلاً لتجنب إغلاق أوراكل للخمول
def cpu_stress():
    while True:
        math.factorial(10000)
        time.sleep(10)

# --- 2. إعدادات البوت ---
API_TOKEN = os.getenv('BOT_TOKEN')
SNAP_URL = os.getenv('SNAP_URL')
bot = telebot.TeleBot(API_TOKEN)

# --- 3. الدوال البرمجية (Downloader Logic) ---

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "أهلاً بك! أرسل لي رابط فيديو من (تيك توك، إنستقرام، سناب شات) وسأقوم بتحميله لك فوراً.")

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    url = message.text
    if "tiktok.com" in url or "instagram.com" in url or "snapchat.com" in url:
        msg = bot.reply_to(message, "جاري المعالجة والتحميل... انتظر قليلاً ⏳")
        
        try:
            ydl_opts = {
                'format': 'best',
                'outtmpl': 'downloaded_video.mp4',
                'quiet': True,
                'no_warnings': True,
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            
            with open('downloaded_video.mp4', 'rb') as video:
                bot.send_video(message.chat.id, video, caption=f"تم التحميل بنجاح ✅\n\nتابعني على سناب: {SNAP_URL}")
            
            bot.delete_message(message.chat.id, msg.message_id)
            os.remove('downloaded_video.mp4') # مسح الفيديو لتوفير المساحة
            
        except Exception as e:
            bot.edit_message_text(f"حدث خطأ أثناء التحميل: {str(e)}", message.chat.id, msg.message_id)
    else:
        bot.reply_to(message, "عذراً، هذا الرابط غير مدعوم حالياً.")

# --- 4. تشغيل السيرفر والبوت ---
def run_flask():
    app.run(host='0.0.0.0', port=8080)

if __name__ == "__main__":
    # تشغيل Flask في خلفية العمل
    Thread(target=run_flask).start()
    # تشغيل دالة الجهد للمعالج
    Thread(target=cpu_stress).start()
    
    print("البوت بدأ العمل الآن على أوراكل... 🚀")
    bot.infinity_polling()
