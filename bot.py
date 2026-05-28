import os
import subprocess
import shutil
import zipfile
import logging
import telebot
from telebot import apihelper
from dotenv import load_dotenv

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
load_dotenv()

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
proxy_url = os.getenv("TELEGRAM_PROXY")

if proxy_url:
    apihelper.proxy = {'https': proxy_url}
    logger.info(f"Proxy enabled:{proxy_url}")
if not TOKEN or not CHAT_ID:
    logger.critical("ERROR in .env file(TOKEN and CHAT_ID not found)")
    exit(1)
    
bot = telebot.TeleBot(TOKEN)

def check_visitor(func):
    def wrapper(message, *args, **kwargs):
        if str(message.chat.id) != CHAT_ID:
            logger.warning(f"Wrong CHAT_ID. ID: {message.chat.id}, User: @{message.from_user.username}")
            bot.send_message(message.chat.id, "You cannot do that")
            return
        return func(message, *args, **kwargs)
    return wrapper

@bot.message_handler(commands=['start'])
def start(message):
    logger.info(f"Command /start from {message.chat.id}")
    bot.send_message(message.chat.id, "Bot is ready")
    
@bot.message_handler(commands=['scr'])
@check_visitor
def take_screenshot(message):
    logger.info(f"Command /scr from {message.chat.id}")
    bot.send_message(message.chat.id, "Taking screenshot")

@bot.message_handler(commands=['say'])
@check_visitor
def speak(message):
    logger.info(f"Command /say from {message.chat.id}")
    text = message.text.replace('/say','').strip()
    if not text:
        bot.send_message(message.chat.id, "Empty after /say")
        return
    ps1 = f"""Add-Type -AssemblyName System.Speech;
            (New-Object System.Speech.Synthesis.SpeechSynthesizer).Speak('{text}')"""
    subprocess.run(["powershell.exe","-Command", ps1])
    bot.send_message(message.chat.id, f"Said that: {text}")
    
@bot.message_handler(commands=['backup'])
@check_visitor
def speak(message):
    logger.info(f"Command /backup from {message.chat.id}")
    bot.send_message(message.chat.id, "Start building")
    zip_name = "linux_backup.zip"
    files_to_back = ["smart_sorter.py","bot_remote.py",".zshrc"]

    try:
        with zipfile.ZipFile(zip_name, 'w') as zipf:
            for file in files_to_back:
                full_path = os.path.expanduser(f"~/{file}")
                if os.path.exists(full_path):
                    zipf.write(full_path, arcname=file)
                    logger.info(f"file zipped")
                else:
                    logger.warning(f"file not foundd")
        logger.info("backup sending")
        with open(zip_name, 'rb') as f:
            bot.send_document(message.chat.id, f ,caption = "Backup")

        win_path = os.getenv("BACKUP_WIN_PATH", os.path.expanduser("~/LinuxBackup"))

        os.makedirs(win_path, exist_ok=True)
        shutil.copy(zip_name, os.path.join(win_path, zip_name))
        logger.info(f"Copy saved: {win_path}")
        os.remove(zip_name)
        logger.info("/backup finished")

    except Exception as err:
        logger.error(f"erroe:{err}")
        bot.send_message(message.chat.id, f"error:{err}")

@bot.message_handler(func=lambda m: True)
def echo_all(message):
    logger.info(f"Message from {message.chat.id}: {message.text}")

logger.info("Bot is ready")
bot.infinity_polling()
