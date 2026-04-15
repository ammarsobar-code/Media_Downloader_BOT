import os
import telebot
import yt_dlp
import requests
from threading import Thread
from flask import Flask
from dotenv import load_dotenv
from telebot.types import InputMediaPhoto

load_dotenv()

app = Flask('')
@app.route('/')
def home(): return "Bot is running!"

API_TOKEN = os.getenv('BOT_TOKEN')
SNAP_URL = os.getenv('SNAP_URL')
bot = telebot.TeleBot(API_TOKEN)

def download_media(url):
    ydl_opts = {
        'format': 'best',
        'quiet': True,
        'no_warnings': True,
        'nocheckcertificate': True,
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
    }
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        
        # التعامل مع كاروسيل تيك توك (صور متعددة)
        if 'entries' in info or info.get('protocol') == 'https_paged_list' or info.get('type') == 'playlist':
            images = []
            for entry in info.get('entries', []):
                if entry.get('url'): images.append(entry['url'])
            return "images", images[:10] # نحدد أول 10 صور فقط لتجنب السبام
            
        # التحقق إذا كان المحتوى صورة واحدة (سناب شات أحياناً)
        if info.get('ext') in ['jpg', 'png', 'webp', 'jpeg']:
            return "photo", info['url']
            
        # الوضع الافتراضي: فيديو
        ydl.download([url])
        return "video", "downloaded_video.mp4"

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    url = message.text.strip()
    if any(domain in url for domain in ["tiktok.com", "snapchat.com", "instagram.com"]):
        msg = bot.reply_to(message, "جاري المعالجة... ⏳")
        try:
            media_type, result = download_media(url)
            
            if media_type == "video":
                with open(result, 'rb') as f:
                    bot.send_video(message.chat.id, f, caption=f"تم التحميل ✅\n{SNAP_URL}")
                os.remove(result)
            
            elif media_type == "photo":
                bot.send_photo(message.chat.id, result, caption=f"تم التحميل ✅\n{SNAP_URL}")
                
            elif media_type == "images":
                media_group = [InputMediaPhoto(img) for img in result]
                bot.send_media_group(message.chat.id, media_group)
                bot.send_message(message.chat.id, f"تم تحميل ألبوم الصور بنجاح ✅\n{SNAP_URL}")

            bot.delete_message(message.chat.id, msg.message_id)
        except Exception as e:
            bot.edit_message_text(f"فشل التحميل: {str(e)}", message.chat.id, msg.message_id)

if __name__ == "__main__":
    Thread(target=lambda: app.run(host='0.0.0.0', port=8080)).start()
    bot.infinity_polling()
