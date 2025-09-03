from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import sqlite3, os

# --- Database ---
conn = sqlite3.connect("bot.db", check_same_thread=False)
c = conn.cursor()
c.execute("""CREATE TABLE IF NOT EXISTS users 
             (id INTEGER PRIMARY KEY, username TEXT, vip INTEGER DEFAULT 0)""")
c.execute("""CREATE TABLE IF NOT EXISTS payments 
             (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, trx_id TEXT, status TEXT)""")
conn.commit()

# --- Config (Environment Variables) ---
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))
PAY_NUMBER = os.getenv("PAY_NUMBER")

# --- Commands ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    c.execute("INSERT OR IGNORE INTO users (id, username) VALUES (?, ?)", (user.id, user.username))
    conn.commit()
    keyboard = [["Buy VIP", "My Info"]]
    await update.message.reply_text(
        "မင်္ဂလာပါ 🙌\nVIP ဝယ်ချင်ရင် Buy VIP ကိုနှိပ်ပါ",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )

async def buy_vip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"💎 Buy VIP\n\nKBZPay/WavePay နံပါတ်: {PAY_NUMBER}\n\n"
        "ငွေလွှဲပြီး Transaction ID ကို ဤနေရာတွင် တိုက်ရိုက် ပို့ပေးပါ။"
    )
    context.user_data["awaiting_payment"] = True

async def handle_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get("awaiting_payment"):
        trx_id = update.message.text
        user = update.message.from_user
        c.execute("INSERT INTO payments (user_id, trx_id, status) VALUES (?, ?, ?)", 
                  (user.id, trx_id, "pending"))
        conn.commit()
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=f"💰 Payment Pending\nUser: @{user.username}\nID: {user.id}\nTRX: {trx_id}"
        )
        await update.message.reply_text("✅ Payment တင်သွင်းပြီးပါပြီ။ Admin စစ်ဆေးပေးမည်။")
        context.user_data["awaiting_payment"] = False

async def approve(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id != ADMIN_ID:
        return
    try:
        _, user_id = update.message.text.split()
        c.execute("UPDATE users SET vip=1 WHERE id=?", (user_id,))
        c.execute("UPDATE payments SET status='approved' WHERE user_id=? AND status='pending'", (user_id,))
        conn.commit()
        await context.bot.send_message(chat_id=int(user_id), text="🎉 VIP အောင်မြင်စွာ အတည်ပြုပြီးပါပြီ!")
        await update.message.reply_text("✅ Approved successfully.")
    except:
        await update.message.reply_text("❌ Usage: /approve USER_ID")

async def my_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    c.execute("SELECT vip FROM users WHERE id=?", (user.id,))
    vip = c.fetchone()[0]
    await update.message.reply_text(f"👤 @{user.username}\nVIP: {'✅' if vip else '❌'}")

# --- Main ---
app = Application.builder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("approve", approve))
app.add_handler(MessageHandler(filters.Regex("Buy VIP"), buy_vip))
app.add_handler(MessageHandler(filters.Regex("My Info"), my_info))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_payment))

app.run_polling()
