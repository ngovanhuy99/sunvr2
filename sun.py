import requests
import json
import os
import random
from datetime import datetime, timedelta
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

BOT_TOKEN = 8357910547:AAGdWiYr03KVEu860_lNw3PxNgsG039C5NQ'  # ← Thay bằng token bot thật
ADMIN_ID = 7071414779

job_refs = {}
last_sent_phien = {}
history = []
DATA_FILE = 'data.json'

def load_data():
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'w') as f:
            json.dump({"keys": {}, "users": {}}, f)
    with open(DATA_FILE, 'r') as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f)

# LẤY API MỚI
def get_api_data():
    try:
        url = "https://apisunbantung-production.up.railway.app"
        res = requests.get(url)
        if res.status_code == 200:
            return res.json()
    except:
        return None

# GỬI KẾT QUẢ KHI PHIÊN MỚI
async def send_result(context: ContextTypes.DEFAULT_TYPE):
    chat_id = context.job.chat_id
    global last_sent_phien, history
    data = get_api_data()
    if not data:
        await context.bot.send_message(chat_id=chat_id, text="❌ Lỗi API!")
        return

    phien = data["phien_truoc"]
    if last_sent_phien.get(chat_id) == phien:
        return

    last_sent_phien[chat_id] = phien
    x1, x2, x3 = data["Dice"]
    ket_qua = data["ket_qua"]
    next_phien = data["phien_hien_tai"]
    next_kq = data["du_doan"]
    tincay = data["do_tin_cay"]
    pattern = data.get("cau", "Không rõ")
    now = datetime.now().strftime("%H:%M:%S %d/%m/%Y")

    msg = f"""<b>🔮 [SUN PREMIUM ] DỰ ĐOÁN PHIÊN MỚI 🔮</b>
╔══════════════════╗
║<b>PHIÊN CŨ:</b> {phien}
║<b>🎲XÚC XẮC:</b> {x1} - {x2} - {x3} | <b>KẾT QUẢ:</b> {ket_qua}
╠══════════════════╣
║<b>PHIÊN MỚI: {next_phien}:</b>
║<b>DỰ ĐOÁN : {next_kq}</b>
║<b>ĐỘ TIN CẬY: {tincay}%</b>
║<b>🧩 PATTERN : </b> {pattern}
╠══════════════════╣
║<b>👥️ Hệ Thống Phân Tích Nâng Cao By Thầy Tùng  👥️</b>
║<b>💎 Uy Tín - Chính Xác - Hiệu Quả 💎</b>
╚══════════════════╝"""
    history.insert(0, msg)
    history = history[:100]
    await context.bot.send_message(chat_id=chat_id, text=msg, parse_mode="HTML")

# LỆNH TELE
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🌟 <b> HƯỚNG DẪN SỬ DỤNG {user} 🌟 </b> \n📦 <b> Gói Hiện Tại : ... </b> \n🔴 <b>Các Lệnh Có Sẵn: </b> \n✅️/start - Đăng Kí Và Bắt Đầu\n💲/model - Xem Thông Tin Gói\n🔑/key [mã key] - kích hoạt gói\n🎮/chaybot - Chạy Bot WANIN\n🔮/sunbotnew - Chạy Dự Đoán ( Mô Hình Sun )\n💎/newhitmd5 - Chạy Dự Đoán ( MÔ HÌNH MD5 )\n🔴/stop - Dừng Dự Đoán\n🛠/admin - Lệnh Dành Cho Admin\n📫 <b> Liên Hệ: </b> \n👤<b>Admin: </b> t.me/NguyenTung2029")

async def chaybot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user_id = str(update.effective_user.id)
    data = load_data()
    user_data = data.get("users", {}).get(user_id)

    if not user_data or datetime.now() > datetime.strptime(user_data["hsd"], "%Y-%m-%d"):
        return await update.message.reply_text("❌ Bạn chưa có key hợp lệ. Dùng /key <mã key> để nhập.")

    if chat_id in job_refs:
        return await update.message.reply_text("⚠️ Bot đã chạy rồi.")

    job = context.job_queue.run_repeating(send_result, interval=2, first=1, chat_id=chat_id)
    job_refs[chat_id] = job
    await update.message.reply_text("✅ Bot đã bắt đầu gửi kết quả!")

async def tatbot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if chat_id in job_refs:
        job_refs[chat_id].schedule_removal()
        del job_refs[chat_id]
        await update.message.reply_text("⛔ Bot đã dừng.")
    else:
        await update.message.reply_text("⚠️ Bot chưa chạy.")

async def key(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 1:
        return await update.message.reply_text("📌 Dùng: /key <mã key>")
    user_id = str(update.effective_user.id)
    ma_key = context.args[0]

    data = load_data()
    if ma_key not in data["keys"]:
        return await update.message.reply_text("❌ Key không tồn tại.")
    if data["keys"][ma_key]["used"]:
        return await update.message.reply_text("❌ Key đã được sử dụng.")

    hsd = data["keys"][ma_key]["hsd"]
    data["keys"][ma_key]["used"] = True
    data["users"][user_id] = {"key": ma_key, "hsd": hsd}
    save_data(data)

    await update.message.reply_text(f"✅ Key đã kích hoạt!\n📅 Hạn dùng: {hsd}\nGõ /chaybot để nhận dự đoán.")

async def addkey(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return await update.message.reply_text("⛔ Không có quyền.")
    if len(context.args) < 2:
        return await update.message.reply_text("📌 /addkey <key> <số ngày>")

    key, days = context.args[0], int(context.args[1])
    data = load_data()
    data["keys"][key] = {
        "hsd": (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d"),
        "used": False
    }
    save_data(data)
    await update.message.reply_text(f"✅ Key {key} đã tạo, hạn {days} ngày.")

async def history_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not history:
        return await update.message.reply_text("📭 Chưa có lịch sử.")
    for msg in history[:10]:
        await update.message.reply_text(msg, parse_mode="HTML")

async def ktrakey(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    data = load_data()
    if user_id not in data["users"]:
        return await update.message.reply_text("❌ Bạn chưa kích hoạt key.")
    hsd = data["users"][user_id]["hsd"]
    await update.message.reply_text(f"📅 Key của bạn còn hạn đến: {hsd}")

# CHẠY BOT
from telegram.ext import Application

app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("chaybot", chaybot))
app.add_handler(CommandHandler("tatbot", tatbot))
app.add_handler(CommandHandler("key", key))
app.add_handler(CommandHandler("ktrakey", ktrakey))
app.add_handler(CommandHandler("history", history_cmd))
app.add_handler(CommandHandler("addkey", addkey))

print("✅ BOT ĐANG CHẠY...")
app.run_polling()