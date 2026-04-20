import os, telebot, yt_dlp, time, requests, math
from threading import Thread
from flask import Flask
from fake_useragent import UserAgent
from telebot.types import InputMediaPhoto, InlineKeyboardMarkup, InlineKeyboardButton
from dotenv import load_dotenv

load_dotenv()
app = Flask('')
ua = UserAgent()
USERS_FILE = "users.txt"

# --- الإعدادات الأساسية ---
DAYS_TO_EXPIRE = 2  # التفعيل كل يومين
ADMIN_ID = 5148560761  # ضع الـ ID الخاص بك هنا

@app.route('/')
def home(): return "Bot is running!"

def cpu_stress():
    while True:
        math.factorial(5000)
        time.sleep(30)

def save_user(user_id):
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

# --- محركات التحميل ---
def handle_tiktok(url, chat_id, bot):
    try:
        api_url = f"https://www.tikwm.com/api/?url={url}"
        response = requests.get(api_url, headers={'User-Agent': ua.random}).json()
        if response.get('code') == 0:
            data = response['data']
            if 'images' in data and data['images']:
                media_group = [InputMediaPhoto(img) for img in data['images'][:10]]
                bot.send_media_group(chat_id, media_group)
                return True
            elif 'play' in data:
                bot.send_video(chat_id, data['play']) 
                return True
    except: pass
    return False

def handle_snap_or_fallback(url, chat_id, bot):
    ydl_opts = {
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'quiet': True, 'user_agent': ua.random, 'noplaylist': True,
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            video_url = info.get('url')
            if 'entries' in info and info['entries']:
                video_url = info['entries'][-1].get('url')
            if video_url:
                bot.send_video(chat_id, video_url) 
                return True
    except: pass
    return False

# --- منطق البوت والتحقق ---
API_TOKEN = os.getenv('BOT_TOKEN')
SNAP_URL_VAR = os.getenv('SNAP_URL', 'https://snapchat.com/')
bot = telebot.TeleBot(API_TOKEN)
user_status = {} # {user_id: {"status": 2, "time": timestamp}}

def is_user_verified(uid):
    if uid in user_status and user_status[uid].get("status") == 2:
        elapsed = (time.time() - user_status[uid].get("time", 0)) / (24 * 3600)
        if elapsed < DAYS_TO_EXPIRE: return True
    return False

def get_verify_markup():
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("متابعة الحساب 👻", url=SNAP_URL_VAR))
    markup.add(InlineKeyboardButton("تفعيل البوت 🔓", callback_data="verify_user"))
    return markup

@bot.message_handler(commands=['start'])
def send_welcome(message):
    save_user(message.chat.id)
    bot.send_message(message.chat.id, "أهلاً بك! لتفعيل البوت يرجى متابعة حسابي في سناب شات أولاً 👻", reply_markup=get_verify_markup())

@bot.message_handler(commands=['admin'])
def admin_panel(message):
    if message.chat.id == ADMIN_ID:
        bot.reply_to(message, f"📊 عدد المستخدمين الكلي: {get_users_count()}")

@bot.callback_query_handler(func=lambda call: call.data == "verify_user")
def verify_callback(call):
    uid = call.message.chat.id
    current = user_status.get(uid, {}).get("status", 0)

    if current == 0:
        user_status[uid] = {"status": 1, "time": time.time()}
        bot.edit_message_text("⚠️ لم يتم التحقق! تأكد من المتابعة ثم اضغط تفعيل مرة أخرى ليتأكد النظام.", uid, call.message.message_id, reply_markup=get_verify_markup())
    else:
        user_status[uid] = {"status": 2, "time": time.time()}
        bot.delete_message(uid, call.message.message_id) # حذف رسالة التحقق ليبقى الشات نظيفاً
        bot.send_message(uid, "✅ تم التفعيل بنجاح! أرسل الرابط الآن..")

@bot.message_handler(func=lambda message: True)
def main_handler(message):
    uid = message.chat.id
    if not is_user_verified(uid):
        user_status[uid] = {"status": 0, "time": 0}
        send_welcome(message)
        return

    url = message.text.strip()
    if any(domain in url for domain in ["tiktok.com", "snapchat.com", "v.it7.to"]):
        msg = bot.reply_to(message, "جاري التحميل... ⏳")
        success = handle_tiktok(url, uid, bot) if "tiktok.com" in url else handle_snap_or_fallback(url, uid, bot)
        if success: bot.delete_message(uid, msg.message_id)
        else: bot.edit_message_text("عذراً، فشل التحميل أو الرابط غير مدعوم 🛠️", uid, msg.message_id)
    else:
        bot.reply_to(message, "يرجى إرسال رابط صحيح ❌")

if __name__ == "__main__":
    Thread(target=lambda: app.run(host='0.0.0.0', port=8080)).start()
    Thread(target=cpu_stress).start()
    bot.infinity_polling()
