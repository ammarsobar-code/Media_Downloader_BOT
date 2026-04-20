import os, telebot, yt_dlp, time, requests, math
from threading import Thread
from flask import Flask
from fake_useragent import UserAgent
from telebot.types import InputMediaPhoto, InlineKeyboardMarkup, InlineKeyboardButton
from dotenv import load_dotenv

# تحميل المتغيرات السرية من ملف .env
load_dotenv()

app = Flask('')
ua = UserAgent()
USERS_FILE = "users.txt"

# --- المتغيرات الأساسية (يمكنك تعديلها) ---
DAYS_TO_EXPIRE = 2 
ADMIN_ID = 5148560761  # تأكد من وضع ID حسابك هنا ليعمل أمر الإحصائيات

@app.route('/')
def home(): return "Bot is Alive!"

def cpu_stress():
    """كود لإبقاء المعالج نشطاً لحماية السيرفر من الإغلاق في أوراكل"""
    while True:
        math.factorial(5000)
        time.sleep(30)

def save_user(user_id):
    """تسجيل المستخدمين في ملف نصي للإحصائيات"""
    if not os.path.exists(USERS_FILE):
        with open(USERS_FILE, "w") as f: pass
    with open(USERS_FILE, "r") as f:
        users = f.read().splitlines()
    if str(user_id) not in users:
        with open(USERS_FILE, "a") as f:
            f.write(str(user_id) + "\n")

def get_users_count():
    """قراءة عدد المستخدمين الإجمالي"""
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
                bot.send_video(chat_id, data['play'], caption="") 
                return True
    except: pass
    return False

def handle_snap_or_fallback(url, chat_id, bot):
    ydl_opts = {
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'quiet': True, 'user_agent': ua.random, 'noplaylist': True,
        'outtmpl': f'vid_{chat_id}_%(id)s.%(ext)s'
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            if os.path.exists(filename):
                with open(filename, 'rb') as video:
                    bot.send_video(chat_id, video)
                os.remove(filename) # تنظيف الملف بعد الإرسال
                return True
    except: pass
    return False

# --- إعدادات البوت ومنطق التحقق ---

API_TOKEN = os.getenv('BOT_TOKEN')
SNAP_URL_VAR = os.getenv('SNAP_URL', 'https://snapchat.com/')
bot = telebot.TeleBot(API_TOKEN)
user_status = {} # تخزين حالة المستخدم ووقت التفعيل

def is_user_verified(uid):
    """فحص هل المستخدم مفعل وهل مرت يومين على تفعيله"""
    if uid in user_status and user_status[uid].get("status") == 2:
        elapsed = (time.time() - user_status[uid].get("time", 0)) / (24 * 3600)
        if elapsed < DAYS_TO_EXPIRE: return True
    return False

def get_verify_markup():
    """توليد أزرار المتابعة والتحقق"""
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("متابعة الحساب 👻", url=SNAP_URL_VAR))
    markup.add(InlineKeyboardButton("تفعيل البوت 🔓", callback_data="verify_user"))
    return markup

@bot.message_handler(commands=['start'])
def send_welcome(message):
    save_user(message.chat.id)
    text = (
        "أهلاً بك في بوت التحميل 📥\n\n"
        "لتفعيل ميزات البوت، يرجى متابعة حسابي في سناب شات أولاً 👻"
    )
    bot.send_message(message.chat.id, text, reply_markup=get_verify_markup())

@bot.message_handler(commands=['admin'])
def admin_panel(message):
    if message.chat.id == ADMIN_ID:
        count = get_users_count()
        bot.reply_to(message, f"📊 إحصائيات البوت:\n\nعدد المستخدمين الإجمالي: {count}")

@bot.callback_query_handler(func=lambda call: call.data == "verify_user")
def verify_callback(call):
    uid = call.message.chat.id
    current = user_status.get(uid, {}).get("status", 0)

    if current == 0:
        # الخطوة الأولى: نرسل رسالة جديدة بالأزرار لتكون أكثر واقعية
        user_status[uid] = {"status": 1, "time": time.time()}
        bot.answer_callback_query(call.id, "فحص سجلات المتابعة...")
        
        fail_text = (
            "⚠️ لم يتم التحقق من متابعتك في سجلاتنا اللحظية.\n\n"
            "يرجى التأكد من ضغط زر 'متابعة الحساب' بالأعلى، ثم اضغط على زر 'تفعيل البوت' أدناه مرة أخرى للتأكيد."
        )
        bot.send_message(uid, fail_text, reply_markup=get_verify_markup())
    
    elif current == 1:
        # الخطوة الثانية: التفعيل الفعلي لمدة يومين
        user_status[uid] = {"status": 2, "time": time.time()}
        bot.answer_callback_query(call.id, "تم التفعيل بنجاح! ✅")
        bot.send_message(uid, "✨ تهانينا! تم تفعيل ميزات البوت لك بنجاح لمدة يومين.\nأرسل الآن أي رابط من سناب شات أو تيك توك.")

@bot.message_handler(func=lambda message: True)
def main_handler(message):
    uid = message.chat.id
    url = message.text.strip()

    # إذا لم يكن المستخدم مفعل (أو انتهت اليومين)
    if not is_user_verified(uid):
        user_status[uid] = {"status": 0, "time": 0}
        send_welcome(message)
        return

    if any(domain in url for domain in ["tiktok.com", "snapchat.com", "v.it7.to"]):
        msg = bot.reply_to(message, "جاري التحميل... ⏳")
        success = handle_tiktok(url, uid, bot) if "tiktok.com" in url else handle_snap_or_fallback(url, uid, bot)
        
        if success:
            bot.delete_message(uid, msg.message_id)
        else:
            bot.edit_message_text("عذراً، فشل التحميل. تأكد من أن الحساب عام والرابط صحيح 🛠️", uid, msg.message_id)
    else:
        bot.reply_to(message, "يرجى إرسال رابط صحيح من سناب شات أو تيك توك ❌")

if __name__ == "__main__":
    # تشغيل سيرفر الويب والمعالج في Threads منفصلة
    Thread(target=lambda: app.run(host='0.0.0.0', port=8080)).start()
    Thread(target=cpu_stress).start()
    print("Downloader Bot is running...")
    bot.infinity_polling()
