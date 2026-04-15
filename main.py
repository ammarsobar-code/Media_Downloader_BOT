import os
import telebot
import yt_dlp
import time
import requests
import json
from datetime import datetime, timedelta
from threading import Thread
from flask import Flask
from fake_useragent import UserAgent
from telebot.types import InputMediaPhoto, InlineKeyboardMarkup, InlineKeyboardButton
from dotenv import load_dotenv

# تحميل المتغيرات البيئية
load_dotenv()

# --- 1. إعدادات السيرفر والبيانات ---
app = Flask('')
ua = UserAgent()
DATA_FILE = 'users_data.json'

def load_data():
    """تحميل بيانات المستخدمين من ملف JSON لضمان عدم ضياع التفعيل"""
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_data(data):
    """حفظ بيانات المستخدمين في ملف JSON"""
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f)

# تحميل البيانات عند بدء التشغيل
user_data = load_data()

@app.route('/')
def home():
    return "Bot is running on Oracle Cloud!"

# --- 2. محركات التحميل ---

def handle_tiktok(url, chat_id, bot):
    try:
        api_url = f"https://www.tikwm.com/api/?url={url}"
        headers = {'User-Agent': ua.random}
        response = requests.get(api_url, headers=headers).json()

        if response.get('code') == 0:
            data = response['data']
            if 'images' in data and data['images']:
                images = data['images']
                media_group = [InputMediaPhoto(img_url) for img_url in images[:10]]
                bot.send_media_group(chat_id, media_group)
                return True
            elif 'play' in data:
                video_url = data['play']
                bot.send_video(chat_id, video_url, caption="") 
                return True
    except: pass
    return False

def handle_snap_or_fallback(url, chat_id, bot):
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
    except: pass
    return False

# --- 3. إعدادات البوت والتحقق الدوري (3 أيام) ---

API_TOKEN = os.getenv('BOT_TOKEN')
SNAP_URL_VAR = os.getenv('SNAP_URL', 'https://snapchat.com/')
bot = telebot.TeleBot(API_TOKEN)

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
    uid = str(call.message.chat.id)
    user_info = user_data.get(uid, {})
    status = user_info.get('status', 0)

    if status == 0:
        user_data[uid] = {'status': 1, 'last_verify': ''}
        save_data(user_data)
        bot.send_message(uid, "لم يتم التحقق من متابعتك لحسابي ⚠️\nتأكد من المتابعة ثم اضغط تفعيل مجدداً 👻", reply_markup=get_verify_markup())
    else:
        # تفعيل ناجح وحفظ التاريخ الحالي
        user_data[uid] = {
            'status': 2,
            'last_verify': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        save_data(user_data)
        bot.answer_callback_query(call.id, "تم التفعيل! ✅")
        bot.send_message(uid, "تم تفعيل البوت بنجاح، يمكنك الآن إرسال الرابط ✅")

@bot.message_handler(func=lambda message: True)
def main_handler(message):
    uid = str(message.chat.id)
    url = message.text.strip()

    # فحص الصلاحية (3 أيام)
    is_verified = False
    if uid in user_data and user_data[uid].get('status') == 2:
        last_verify_str = user_data[uid].get('last_verify')
        try:
            last_verify_date = datetime.strptime(last_verify_str, "%Y-%m-%d %H:%M:%S")
            if datetime.now() < last_verify_date + timedelta(days=3):
                is_verified = True
        except: pass

    if not is_verified:
        send_welcome(message)
        return

    if "tiktok.com" in url or "snapchat.com" in url or "v.it7.to" in url:
        prog = bot.reply_to(message, "جاري التحميل... ⏳")
        success = False
        try:
            if "tiktok.com" in url:
                success = handle_tiktok(url, uid, bot)
            
            if not success:
                success = handle_snap_or_fallback(url, uid, bot)

            if success:
                bot.delete_message(uid, prog.message_id)
            else:
                bot.edit_message_text("نواجه مشكلة تقنية حالياً 🛠️", uid, prog.message_id)
        except:
            bot.edit_message_text("نواجه مشكلة تقنية حالياً 🛠️", uid, prog.message_id)
    else:
        bot.reply_to(message, "رابط غير صحيح ❌")

# --- 4. التشغيل النهائي ---
def run_flask():
    app.run(host='0.0.0.0', port=8080)

if __name__ == "__main__":
    Thread(target=run_flask).start()
    print("البوت يعمل بنظام التفعيل كل 3 أيام... 🚀")
    bot.infinity_polling()
