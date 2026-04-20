import os
import telebot
import yt_dlp
import time
import requests
import json
import hashlib
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
ALTERNATIVE_BOT = "@SnapTok_down_bot" 

# --- المتغيرات القابلة للتعديل ---
DAYS_TO_EXPIRE = 2  # مدة التفعيل (أيام)
ADMIN_ID = 5148560761  # <--- ضع الـ ID الخاص بك هنا

def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_data(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f)

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
                bot.send_video(chat_id, data['play'], caption="") 
                return True
    except: pass
    return False

def handle_snap_or_fallback(url, chat_id, bot):
    ydl_opts = {
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'quiet': True,
        'no_warnings': True,
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
        'nocheckcertificate': True,
        'noplaylist': True,
        'merge_output_format': 'mp4',
        'outtmpl': f'vid_{chat_id}_%(id)s.%(ext)s'
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            if os.path.exists(filename):
                with open(filename, 'rb') as video:
                    bot.send_video(chat_id, video)
                os.remove(filename)
                return True
    except: pass
    return False

# --- 3. إعدادات البوت والتحقق الدوري ---

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
    uid = str(message.chat.id)
    if uid not in user_data:
        user_data[uid] = {'status': 0, 'last_verify': ''}
        save_data(user_data)
        
    welcome_text = (
        "أهلاً بك في بوت التحميل 📥\n"
        "هذا البوت يدعم سناب شات و تيك توك 📲\n\n"
        "لتفعيل البوت يتطلب متابعة حسابي في سناب شات أولاً 👻"
    )
    bot.send_message(message.chat.id, welcome_text, reply_markup=get_verify_markup())

@bot.message_handler(commands=['admin'])
def admin_panel(message):
    if message.chat.id == ADMIN_ID:
        count = len(user_data)
        bot.reply_to(message, f"📊 إحصائيات البوت:\n\nعدد المستخدمين الإجمالي: {count}")

@bot.callback_query_handler(func=lambda call: call.data == "verify_user")
def verify_callback(call):
    uid = str(call.message.chat.id)
    user_info = user_data.get(uid, {'status': 0})
    status = user_info.get('status', 0)

    if status == 0:
        # الخطوة الأولى: تنبيه وتحديث الحالة لـ 1
        user_data[uid] = {'status': 1, 'last_verify': ''}
        save_data(user_data)
        bot.answer_callback_query(call.id, "جاري الفحص...")
        
        fail_text = "⚠️ لم يتم التحقق من متابعتك! تأكد من المتابعة ثم اضغط تفعيل مجدداً 👻"
        bot.send_message(uid, fail_text, reply_markup=get_verify_markup())
    else:
        # الخطوة الثانية: التفعيل الفعلي لمدة يومين (أو القيمة المحددة)
        user_data[uid] = {
            'status': 2,
            'last_verify': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        save_data(user_data)
        bot.answer_callback_query(call.id, "تم التفعيل! ✅")
        bot.send_message(uid, "✅ تم تفعيل البوت بنجاح ، يمكنك الآن إرسال الروابط.")

@bot.message_handler(func=lambda message: True)
def main_handler(message):
    uid = str(message.chat.id)
    url = message.text.strip()
    error_msg = f"نواجه مشكلة تقنية حالياً أو الرابط غير مدعوم 🛠️\nيمكنكم استخدام البوت البديل: {ALTERNATIVE_BOT}"

    is_verified = False
    if uid in user_data and user_data[uid].get('status') == 2:
        last_verify_str = user_data[uid].get('last_verify')
        try:
            last_verify_date = datetime.strptime(last_verify_str, "%Y-%m-%d %H:%M:%S")
            if datetime.now() < last_verify_date + timedelta(days=DAYS_TO_EXPIRE):
                is_verified = True
        except: pass

    if not is_verified:
        user_data[uid] = {'status': 0, 'last_verify': ''} # إعادة تعيين إذا انتهت المدة
        save_data(user_data)
        send_welcome(message)
        return

    if any(domain in url for domain in ["tiktok.com", "snapchat.com", "v.it7.to"]):
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
                bot.edit_message_text(error_msg, uid, prog.message_id)
        except:
            bot.edit_message_text(error_msg, uid, prog.message_id)
    else:
        bot.reply_to(message, "رابط غير صحيح ❌ يرجى إرسال روابط سناب أو تيك توك.")

# --- 4. حماية السيرفر من الخمول (Oracle Keep Alive) ---

def keep_cpu_busy():
    while True:
        for _ in range(70000):
            hashlib.sha256(b"active_session").hexdigest()
        time.sleep(15)

# --- 5. التشغيل النهائي ---

def run_flask():
    app.run(host='0.0.0.0', port=5000)

if __name__ == "__main__":
    Thread(target=run_flask, daemon=True).start()
    Thread(target=keep_cpu_busy, daemon=True).start()
    print("البوت يعمل ونظام الحماية نشط... 🚀")
    bot.infinity_polling()
