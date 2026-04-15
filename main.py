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

# --- 1. إعدادات السيرفر والبوت ---
app = Flask('')
ua = UserAgent()

@app.route('/')
def home():
    return "Bot is running on Oracle Cloud!"

def cpu_stress():
    """دالة لرفع استهلاك المعالج قليلاً لتجنب إغلاق أوراكل للسيرفر الخامل"""
    while True:
        math.factorial(5000)
        time.sleep(30)

# --- 2. محركات التحميل ---

def handle_tiktok(url, chat_id, bot):
    try:
        # استخدام API خارجي لدعم الصور (Carousel) والفيديو بدون علامة مائية
        api_url = f"https://www.tikwm.com/api/?url={url}"
        headers = {'User-Agent': ua.random}
        response = requests.get(api_url, headers=headers).json()

        if response.get('code') == 0:
            data = response['data']
            # التحقق إذا كان كاروسيل (صور)
            if 'images' in data and data['images']:
                images = data['images']
                media_group = []
                for img_url in images[:10]:
                    media_group.append(InputMediaPhoto(img_url))
                bot.send_media_group(chat_id, media_group)
                return True
            # التحقق إذا كان فيديو
            elif 'play' in data:
                video_url = data['play']
                bot.send_video(chat_id, video_url, caption="") 
                return True
    except:
        pass
    return False

def handle_snap_or_fallback(url, chat_id, bot):
    # إعدادات محسنة للسناب شات لضمان الجودة والأبعاد الصحيحة
    ydl_opts = {
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'quiet': True,
        'no_warnings': True,
        'user_agent': ua.random,
        'nocheckcertificate': True,
        'noplaylist': True,
        'merge_output_format': 'mp4',
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            video_url = info.get('url')
            if 'entries' in info and info['entries']:
                valid_entries = [e for e in info['entries'] if e]
                if valid_entries: video_url = valid_entries[-1].get('url')

            if video_url:
                bot.send_video(chat_id, video_url, caption="") 
                return True
    except:
        pass
    return False

# --- 3. إعدادات البوت والتحقق ---

API_TOKEN = os.getenv('BOT_TOKEN')
SNAP_URL_VAR = os.getenv('SNAP_URL', 'https://snapchat.com/')

bot = telebot.TeleBot(API_TOKEN)
user_status = {}

def get_verify_markup():
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("متابعة الحساب 👻", url=SNAP_URL_VAR))
    markup.add(InlineKeyboardButton("تفعيل البوت 🔓", callback_data="verify_user"))
    return markup

@bot.message_handler(commands=['start'])
def send_welcome(message):
    welcome_text = (
        "أهلاً بك في بوت التحميل 📥\n"
        "هذا البوت يدعم سناب شات و تيك توك 📲\n\n"
        "لتفعيل البوت يتطلب متابعة حسابي في سناب شات أولاً 👻"
    )
    bot.send_message(message.chat.id, welcome_text, reply_markup=get_verify_markup())

@bot.callback_query_handler(func=lambda call: call.data == "verify_user")
def verify_callback(call):
    uid = call.message.chat.id
    # منطق تفعيل وهمي (يحتاج ضغطتين للتفعيل كما في كود Railway)
    status = user_status.get(uid, 0)

    if status == 0:
        user_status[uid] = 1
        fail_text = (
            "لم يتم التحقق من متابعتك لحسابي ⚠️\n"
            "الرجاء التأكد من متابعة حسابي في سناب شات 👻"
        )
        bot.send_message(uid, fail_text, reply_markup=get_verify_markup())
        bot.answer_callback_query(call.id)
    else:
        user_status[uid] = 2
        bot.answer_callback_query(call.id, "تم التفعيل! ✅")
        bot.send_message(uid, "تم تفعيل البوت يمكنك الآن ارسال الرابط ✅")

@bot.message_handler(func=lambda message: True)
def main_handler(message):
    uid = message.chat.id
    url = message.text.strip()

    # التأكد من التفعيل
    if user_status.get(uid) != 2:
        send_welcome(message)
        return

    if "tiktok.com" in url or "snapchat.com" in url or "v.it7.to" in url:
        prog = bot.reply_to(message, "جاري التحميل... ⏳")
        success = False
        try:
            if "tiktok.com" in url:
                success = handle_tiktok(url, uid, bot)
            
            # إذا فشل كـ تيك توك أو كان سناب شات
            if not success:
                success = handle_snap_or_fallback(url, uid, bot)

            if success:
                bot.delete_message(uid, prog.message_id)
            else:
                bot.edit_message_text("نواجه مشكله تقنيه حاليا وسيتم حلها في اقرب وقت 🛠️", uid, prog.message_id)
        except:
            bot.edit_message_text("نواجه مشكله تقنيه حاليا وسيتم حلها في اقرب وقت 🛠️", uid, prog.message_id)
    else:
        bot.reply_to(message, "رابط غير صحيح ❌")

# --- 4. التشغيل النهائي ---
def run_flask():
    app.run(host='0.0.0.0', port=8080)

if __name__ == "__main__":
    Thread(target=run_flask).start()
    Thread(target=cpu_stress).start()
    print("البوت يعمل الآن على أوراكل بكفاءة ريلواي... 🚀")
    bot.infinity_polling()
