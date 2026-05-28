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
    win_temp_path = "C:\\Windows\\Temp\\screenshot.png"
    wsl_img_path = "/mnt/c/Windows/Temp/screenshot.png"
    ps = (
            "[Reflection.Assembly]::LoadWithPartialName('System.Drawing') | Out-Null; "
            "[Reflection.Assembly]::LoadWithPartialName('System.Windows.Forms') | Out-Null; "
            "$bounds = [System.Windows.Forms.Screen]::PrimaryScreen.Bounds; "
            "$bmp = New-Object System.Drawing.Bitmap $bounds.Width, $bounds.Height; "
            "$graphics = [System.Drawing.Graphics]::FromImage($bmp); "
            "$graphics.CopyFromScreen($bounds.X, $bounds.Y, 0, 0, $bounds.Size); "
            f"$bmp.Save('{win_temp_path}', [System.Drawing.Imaging.ImageFormat]::Png); "
            "$graphics.Dispose(); $bmp.Dispose();"
    )
    try:
        if os.path.exists(wsl_img_path):
            os.remove(wsl_img_path)
        subprocess.run(["powershell.exe", "-Command", ps], check=True)
        if os.path.exists(wsl_img_path):
            with open(wsl_img_path, 'rb') as img:
                bot.send_photo(message.chat.id, img, caption="Your screen")
            os.remove(wsl_img_path)
            logger.info("Screen sended")
        else:
            raise FileNotFoundError("Win not create a screen")
    except Exception as e:
        logger.error(f"Error with screen-creating")
        bot.send_message(message.chat.id, f"Cannot make a screen")
        
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
    zip_name = "wsl_home_backup.zip"
    home_dir = os.path.expanduser("~")
    
    ignored_dirs = {'.venv','venv','.git','.cache'}

    try:
        with zipfile.ZipFile(zip_name, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root,dirs, files in os.walk(home_dir):
                dirs[:] = [d for d in dirs if d not in ignored_dirs]

                for file in files:
                    if file == zip_name:
                        continue
                    if os.path.islink(os.path.join(root, file)) or not os.path.exists(os.path.join(root, file)):
                        continue
                    full_path = os.path.join(root, file)
                    arcname = os.path.relpath(full_path, home_dir)

                    if os.path.getsize(full_path) < 25 * 1024 * 1024:
                        zipf.write(full_path, arcname=arcname)
                        
        zip_size_mb = os.path.getsize(zip_name) / (1024 * 1024)
        logger.info(f"Size of backup: {zip_size_mb:.2f} MB")
        
        logger.info("backup sending")
        with open(zip_name, 'rb') as f:
            bot.send_document(message.chat.id, f ,caption = "Backup", timeout=3000)

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
