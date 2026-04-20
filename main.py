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
USERS_FILE = "users.txt"

# --- إعدادات التفعيل (كل يومين) ---
DAYS_TO_EXPIRE = 2  # <--- البوت سيطلب التحقق كل يومين
ADMIN_ID = 51485600761  # <--- ضع الـ ID الخاص بك هنا ليعمل أمر الإحصائيات

@app.route('/')
def home():
    return "Bot is running on Oracle Cloud!"

def cpu_stress():
    while True:
        math.factorial(5000)
        time.sleep(30)

# --- 2. دوال الإحصائيات والتحقق ---

def save_user(user_id):
    """تسجيل المستخدمين الجدد في ملف نصي"""
    if not os.path.exists(USERS_FILE):
        with open(USERS_FILE, "w") as f: pass
    with open(USERS_FILE, "r") as f:
        users = f.read().splitlines()
    if str(user_id) not in users:
        with open(USERS_FILE, "a") as f:
            f.write(str(user_id) + "\n")

def get_users_count():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, "r") as f:
            return len(f.read().splitlines())
    return 0

# --- 3. محركات التحميل ---

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
                bot.send_video(chat_id, data['play'], caption="") 
                return True
    except: pass
    return False

def handle_snap_or_fallback(url, chat_id, bot):
    ydl_opts = {
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'quiet': True, 'no_warnings': True, 'user_agent': ua.random,
        'nocheckcertificate': True, 'noplaylist': True, 'merge_output_format': 'mp4',
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            video_url = info.get('url')
            if 'entries' in info and info['entries']:
                valid = [e for e in info['entries'] if e]
                if valid: video_url = valid[-1].get('url')
            if video_url:
                bot.send_video(chat_id, video_url, caption="") 
                return True
    except: pass
    return False

# --- 4. منطق التحقق والتحكم ---

API_TOKEN = os.getenv('BOT_TOKEN')
SNAP_URL_VAR = os.getenv('SNAP_URL', 'https://snapchat.com/')

bot = telebot.TeleBot(API_TOKEN)
user_status = {} # {user_id: {"status": 2, "time": timestamp}}

def is_user_verified(uid):
    """فحص هل المستخدم مفعل وهل انتهت اليومين أم لا"""
    if uid in user_status and user_status[uid].get("status") == 2:
        activation_time = user_status[uid].get("time", 0)
        elapsed_days = (time.time() - activation_time) / (24 * 3600)
        if elapsed_days < DAYS_TO_EXPIRE:
            return True
    return False

def get_verify_markup():
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("متابعة الحساب 👻", url=SNAP_URL_VAR))
    markup.add(InlineKeyboardButton("تفعيل البوت 🔓", callback_data="verify_user"))
    return markup

@bot.message_handler(commands=['start'])
def send_welcome(message):
    save_user(message.chat.id)
    welcome_text = (
        "أهلاً بك في بوت التحميل 📥\n"
        "يدعم سناب شات وتيك توك 📲\n\n"
        "لتفعيل البوت يتطلب متابعة حسابي في سناب شات أولاً 👻"
    )
    bot.send_message(message.chat.id, welcome_text, reply_markup=get_verify_markup())

@bot.message_handler(commands=['admin'])
def admin_panel(message):
    if message.chat.id == ADMIN_ID:
        count = get_users_count()
        bot.reply_to(message, f"📊 إحصائيات البوت:\n\nعدد المستخدمين الكلي: {count}")

@bot.callback_query_handler(func=lambda call: call.data == "verify_user")
def verify_callback(call):
    uid = call.message.chat.id
    current_status = user_status.get(uid, {}).get("status", 0)

    if current_status == 0:
        # الخطوة الأولى في التحقق
        user_status[uid] = {"status": 1, "time": time.time()}
        bot.send_message(uid, "لم يتم التحقق من متابعتك! تأكد من المتابعة ثم اضغط تفعيل مرة أخرى ⚠️", reply_markup=get_verify_markup())
        bot.answer_callback_query(call.id)
    elif current_status == 1:
        # الخطوة الثانية: التفعيل النهائي لمدة يومين
        user_status[uid] = {"status": 2, "time": time.time()}
        bot.answer_callback_query(call.id, "تم التفعيل بنجاح لمدة يومين! ✅", show_alert=True)
        bot.send_message(uid, "تم تفعيل البوت، يمكنك الآن إرسال الروابط..")

@bot.message_handler(func=lambda message: True)
def main_handler(message):
    uid = message.chat.id
    url = message.text.strip()

    # التحقق من الصلاحية (كل يومين)
    if not is_user_verified(uid):
        # تصفير الحالة ليضطر للضغط مرتين من جديد
        user_status[uid] = {"status": 0, "time": 0}
        send_welcome(message)
        return

    if any(domain in url for domain in ["tiktok.com", "snapchat.com", "v.it7.to"]):
        prog = bot.reply_to(message, "جاري التحميل... ⏳")
        success = handle_tiktok(url, uid, bot) if "tiktok.com" in url else False
        if not success:
            success = handle_snap_or_fallback(url, uid, bot)

        if success:
            bot.delete_message(uid, prog.message_id)
        else:
            bot.edit_message_text("عذراً، حدث خطأ فني أو الرابط غير مدعوم 🛠️", uid, prog.message_id)
    else:
        bot.reply_to(message, "يرجى إرسال رابط صحيح ❌")

if __name__ == "__main__":
    Thread(target=lambda: app.run(host='0.0.0.0', port=8080)).start()
    Thread(target=cpu_stress).start()
    print("البوت يعمل الآن بنظام اليومين والإحصائيات... 🚀")
    bot.infinity_polling()
