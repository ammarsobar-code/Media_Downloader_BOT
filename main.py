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

# تحميل المتغيرات البيئية
load_dotenv()

# --- 1. إعدادات السيرفر ---
app = Flask('')

@app.route('/')
def home():
    return "Bot is running on Oracle Cloud!"

def cpu_stress():
    while True:
        math.factorial(5000)
        time.sleep(30)

# --- 2. إعدادات البوت ---
API_TOKEN = os.getenv('BOT_TOKEN')
SNAP_URL = os.getenv('SNAP_URL')
bot = telebot.TeleBot(API_TOKEN)

# --- 3. الدوال البرمجية ---

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "أهلاً بك! أرسل لي رابط فيديو من (تيك توك، إنستقرام، سناب شات) وسأقوم بتحميله لك فوراً. 🚀")

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    url = message.text.strip()
    
    # التحقق من المنصات المدعومة
    supported = ["tiktok.com", "instagram.com", "snapchat.com", "v.it7.to"]
    if any(domain in url for domain in supported):
        msg = bot.reply_to(message, "جاري معالجة الرابط وتحميل الفيديو... انتظر قليلاً ⏳")
        
        # إعدادات خاصة لتجاوز حماية سناب شات وتيك توك
        ydl_opts = {
            'format': 'best',
            'outtmpl': 'downloaded_video.mp4',
            'quiet': True,
            'no_warnings': True,
            'nocheckcertificate': True,
            'ignoreerrors': True,
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
            'add_header': [
                'Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
                'Accept-Language: en-US,en;q=0.5',
                'Connection: keep-alive',
            ],
        }
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                
            if os.path.exists('downloaded_video.mp4'):
                with open('downloaded_video.mp4', 'rb') as video:
                    bot.send_video(
                        message.chat.id, 
                        video, 
                        caption=f"تم التحميل بنجاح ✅\n\nلمتابعة صاحب البوت على سناب:\n{SNAP_URL}"
                    )
                bot.delete_message(message.chat.id, msg.message_id)
                os.remove('downloaded_video.mp4')
            else:
                bot.edit_message_text("عذراً، تعذر استخراج الفيديو. تأكد أن الحساب عام (Public) وليس خاصاً.", message.chat.id, msg.message_id)
                
        except Exception as e:
            bot.edit_message_text(f"حدث خطأ فني: {str(e)}", message.chat.id, msg.message_id)
    else:
        bot.reply_to(message, "يرجى إرسال رابط صحيح من تيك توك، سناب شات، أو إنستقرام.")

# --- 4. التشغيل ---
def run_flask():
    app.run(host='0.0.0.0', port=8080)

if __name__ == "__main__":
    # تشغيل الخدمات في الخلفية
    Thread(target=run_flask).start()
    Thread(target=cpu_stress).start()
    
    print("البوت يعمل الآن بأقصى طاقة... 🚀")
    bot.infinity_polling()
