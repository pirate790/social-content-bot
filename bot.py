import sqlite3
import requests
import time
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# ============================================
# REPLACE THESE 2 VALUES ONLY
# ============================================
BOT_TOKEN = "8745420168:AAFN53oGERQ1aCG2zj8QoQHS2sKzRzJNX_c"
TALLY_FORM_LINK = "https://tally.so/r/GxkM8ey"
# ============================================

GROQ_API_KEY = "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"

OPAY_ACCOUNT = "Itoro Etim Sunday"
OPAY_NUMBER = "9160652539"
YOUR_WHATSAPP = "2347071690772"
FREE_TRIAL_LIMIT = 3

SYSTEM_PROMPT = """You are a social media expert who helps Nigerian creators, freelancers, and founders grow on Twitter. 

Given a topic from the user, generate exactly 3 tweets. Follow these rules strictly:

1. Each tweet must be under 270 characters.
2. Each tweet must start with a strong hook (question, bold statement, or relatable pain).
3. Write in clear, conversational English.
4. Include 1-2 relevant hashtags per tweet.
5. Vary the formats: one tip list, one story, one question.
6. Separate the tweets with "---" so they can be easily split.

Always output exactly 3 tweets. No intro, no outro — just the tweets."""

def get_db_connection():
    return sqlite3.connect('users.db')

def get_user(telegram_id):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE telegram_id = ?", (telegram_id,))
    user = c.fetchone()
    conn.close()
    return user

def create_user(telegram_id, first_name, username):
    conn = get_db_connection()
    c = conn.cursor()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute("INSERT OR IGNORE INTO users (telegram_id, first_name, username, trial_count, paid, joined_date) VALUES (?, ?, ?, 0, 0, ?)",
              (telegram_id, first_name, username, now))
    conn.commit()
    conn.close()

def get_trial_count(telegram_id):
    user = get_user(telegram_id)
    if user:
        return user[5] if len(user) > 5 else 0
    return 0

def increment_trial(telegram_id):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("UPDATE users SET trial_count = trial_count + 1 WHERE telegram_id = ?", (telegram_id,))
    conn.commit()
    conn.close()

def is_paid(telegram_id):
    user = get_user(telegram_id)
    if user and user[3] == 1:
        paid_until = user[4]
        if paid_until:
            return datetime.now() < datetime.strptime(paid_until, "%Y-%m-%d %H:%M:%S")
    return False

def can_use_trial(telegram_id):
    return get_trial_count(telegram_id) < FREE_TRIAL_LIMIT

def save_post(telegram_id, prompt, generated):
    conn = get_db_connection()
    c = conn.cursor()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute("INSERT INTO posts (telegram_id, prompt, generated_posts, created_date) VALUES (?, ?, ?, ?)",
              (telegram_id, prompt, generated, now))
    conn.commit()
    conn.close()

def generate_ai_posts(topic):
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "llama-3.1-8b-instant",
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": topic}
        ],
        "max_tokens": 500
    }
    
    for attempt in range(3):
        try:
            response = requests.post(url, headers=headers, json=data, timeout=60)
            result = response.json()
            
            if "choices" in result and len(result["choices"]) > 0:
                return result["choices"][0]["message"]["content"]
            else:
                if attempt < 2:
                    time.sleep(3)
                    continue
                raise Exception(f"API Error: {result}")
        except requests.exceptions.Timeout:
            if attempt < 2:
                time.sleep(5)
                continue
            raise Exception("Network timeout. Please try again.")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    create_user(user.id, user.first_name, user.username or "@unknown")

    welcome_msg = f"""👋🏾 Welcome to ContentSchedulerBot, {user.first_name}!

I write ready-to-post social media content using AI.

Just send me a topic like: "3 tweets about freelancing"

🎁 You have {FREE_TRIAL_LIMIT} FREE posts to try me out!
🔓 After that: ₦2,000/month for unlimited posts

Commands:
/start - Welcome message
/myid - Get your Telegram ID
/status - Check your account status

Send your first topic now!"""

    await update.message.reply_text(welcome_msg)


async def myid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    
    whatsapp_msg = f"Hello! My Telegram ID is: {user.id}%0AUsername: @{user.username or 'N/A'}%0AI want to activate my Pro account."
    whatsapp_link = f"https://wa.me/{YOUR_WHATSAPP}?text={whatsapp_msg}"
    
    keyboard = [[InlineKeyboardButton("📱 Send to WhatsApp", url=whatsapp_link)]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"🆔 Your Telegram ID: `{user.id}`\n\n"
        f"Click the button below to send your ID to us on WhatsApp for activation:",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )


async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    
    whatsapp_msg = f"Hello! I want to upgrade to Pro.%0AMy Telegram ID: {user.id}%0AUsername: @{user.username or 'N/A'}"
    whatsapp_link = f"https://wa.me/{YOUR_WHATSAPP}?text={whatsapp_msg}"
    keyboard = [[InlineKeyboardButton("💬 Upgrade via WhatsApp", url=whatsapp_link)]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if is_paid(user.id):
        user_data = get_user(user.id)
        await update.message.reply_text(f"✅ PRO Member\n📅 Paid until: {user_data[4]}\n♾️ Unlimited posts")
    elif can_use_trial(user.id):
        remaining = FREE_TRIAL_LIMIT - get_trial_count(user.id)
        await update.message.reply_text(
            f"🎁 Free trial active\n✍️ {remaining} post{'s' if remaining > 1 else ''} remaining\n\n"
            f"🔓 Upgrade: ₦2,000/month\n"
            f"Opay | {OPAY_ACCOUNT} | {OPAY_NUMBER}",
            reply_markup=reply_markup
        )
    else:
        await update.message.reply_text(
            f"⚠️ Free trial used up\n\n"
            f"🔓 Unlock Pro: ₦2,000/month\n"
            f"Opay | {OPAY_ACCOUNT} | {OPAY_NUMBER}\n\n"
            f"Or click below to activate via WhatsApp:",
            reply_markup=reply_markup
        )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    topic = update.message.text

    if not get_user(user.id):
        create_user(user.id, user.first_name, user.username or "@unknown")

    if is_paid(user.id) or can_use_trial(user.id):
        await update.message.reply_text("✍️ Generating your posts...")

        try:
            posts = generate_ai_posts(topic)
            save_post(user.id, topic, posts)
            
            if not is_paid(user.id):
                increment_trial(user.id)
                remaining = FREE_TRIAL_LIMIT - get_trial_count(user.id)
                
                if remaining > 0:
                    trial_msg = f"\n\n🎁 {remaining} free post{'s' if remaining > 1 else ''} remaining."
                    await update.message.reply_text(f"Here are your posts:\n\n{posts}{trial_msg}")
                else:
                    whatsapp_msg = f"Hello! I want to upgrade to Pro.%0AMy Telegram ID: {user.id}"
                    whatsapp_link = f"https://wa.me/{YOUR_WHATSAPP}?text={whatsapp_msg}"
                    keyboard = [[InlineKeyboardButton("💬 Upgrade via WhatsApp", url=whatsapp_link)]]
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    
                    trial_msg = (f"\n\n⚠️ Your free trial is over!\n\n"
                                f"🔓 Unlock unlimited posts for ₦2,000/month:\n\n"
                                f"1️⃣ Transfer ₦2,000 to:\n"
                                f"   Opay | {OPAY_ACCOUNT} | {OPAY_NUMBER}\n\n"
                                f"2️⃣ Fill the form:\n"
                                f"   👉 {TALLY_FORM_LINK}\n\n"
                                f"Or click below to activate via WhatsApp:")
                    
                    await update.message.reply_text(
                        f"Here are your posts:\n\n{posts}{trial_msg}",
                        reply_markup=reply_markup
                    )
                    return
            else:
                await update.message.reply_text(f"Here are your posts:\n\n{posts}")
                
        except Exception as e:
            await update.message.reply_text("❌ Error generating posts. Please try again.")
            print(f"Error: {e}")
    else:
        whatsapp_msg = f"Hello! I want to upgrade to Pro.%0AMy Telegram ID: {user.id}"
        whatsapp_link = f"https://wa.me/{YOUR_WHATSAPP}?text={whatsapp_msg}"
        keyboard = [[InlineKeyboardButton("💬 Activate via WhatsApp", url=whatsapp_link)]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        paywall_msg = f"""🔒 Your free trial is over.

To unlock unlimited AI posts for 30 days:

1️⃣ Transfer ₦2,000 to:
   Opay | {OPAY_ACCOUNT} | {OPAY_NUMBER}

2️⃣ Fill this form:
   👉 {TALLY_FORM_LINK}

Or click below to activate via WhatsApp:"""

        await update.message.reply_text(paywall_msg, reply_markup=reply_markup)


def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("myid", myid))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("=" * 40)
    print("✅ Bot is running...")
    print("✅ AI: Groq (Llama 3.1) - Free & Fast")
    print("=" * 40)
    app.run_polling()

if __name__ == "__main__":
    main()
