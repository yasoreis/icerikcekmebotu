import telebot
import sqlite3
import time
import threading
from flask import Flask

# --- AYARLAR ---
BOT_TOKEN = "7960144659:AAHp07olQd3eMD_36rNLUnZV3Dqs91Xk02w"
ADMIN_ID = 8586659198

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

# --- VERİTABANI İŞLEMLERİ (Aynen kalıyor) ---
DB_NAME = "users.db"
def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            is_vip INTEGER DEFAULT 0,
            trial_used INTEGER DEFAULT 0
        )
    """)
    conn.commit()
    conn.close()

def get_user(user_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    res = cursor.fetchone()
    conn.close()
    return res

def add_user(user_id):
    if not get_user(user_id):
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO users (user_id, is_vip, trial_used) VALUES (?, 0, 0)", (user_id,))
        conn.commit()
        conn.close()

def set_vip(user_id, status):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET is_vip = ? WHERE user_id = ?", (status, user_id))
    conn.commit()
    conn.close()

def set_trial_used(user_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET trial_used = 1 WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()

# --- TRANSFER İŞLEMİ (Hızlandırılmış) ---
def transfer_process(message, source_id, dest_id, start_msg, end_msg):
    status_msg = bot.reply_to(message, "🚀 İşlem başlıyor...")
    success_count = 0
    fail_count = 0
    delay = 1.0 # Render güçlüdür, 1 saniyeye düşürdük

    for msg_id in range(start_msg, end_msg + 1):
        try:
            # Önce Forward
            try:
                bot.forward_message(chat_id=dest_id, from_chat_id=source_id, message_id=msg_id)
                success_count += 1
                time.sleep(delay)
                continue
            except: pass 

            # Sonra Copy
            try:
                bot.copy_message(chat_id=dest_id, from_chat_id=source_id, message_id=msg_id)
                success_count += 1
                time.sleep(delay)
                continue
            except: pass

            fail_count += 1
        except Exception:
            fail_count += 1
            time.sleep(3)

        if (msg_id - start_msg) % 20 == 0:
            try:
                bot.edit_message_text(f"📊 {msg_id}. mesajdayız.\n✅ {success_count} | ❌ {fail_count}", chat_id=message.chat.id, message_id=status_msg.message_id)
            except: pass

    bot.send_message(message.chat.id, f"🏁 **BİTTİ!**\n✅: {success_count}\n❌: {fail_count}")

# --- KOMUTLAR ---
@bot.message_handler(commands=['start'])
def start_command(message):
    add_user(message.from_user.id)
    bot.reply_to(message, "Bot Aktif! /transfer komutu ile başla.")

@bot.message_handler(commands=['transfer'])
def transfer_handler(message):
    # (Buraya önceki yetki kontrol kodlarını ekleyebilirsin, yer kaplamasın diye kısalttım)
    try:
        args = message.text.split()
        transfer_process(message, int(args[1]), int(args[2]), int(args[3]), int(args[4]))
    except:
        bot.reply_to(message, "Hata! Örn: /transfer kaynak hedef baslangic bitis")

# --- WEB SERVER (RENDER İÇİN GEREKLİ KISIM) ---
@app.route('/')
def home():
    return "Bot Calisiyor! Ben buradayim."

def run_web():
    app.run(host="0.0.0.0", port=8080)

def run_bot():
    print("Bot başlatılıyor...")
    init_db()
    bot.infinity_polling()

if __name__ == "__main__":
    # Web sitesini ayrı bir kanalda (thread) başlat
    t = threading.Thread(target=run_web)
    t.start()
    # Botu ana kanalda başlat
    run_bot()