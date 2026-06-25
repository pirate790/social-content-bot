import sqlite3
from datetime import datetime, timedelta

print("=" * 40)
print("ACTIVATE A PAID USER")
print("=" * 40)

telegram_id = input("Enter user's Telegram ID: ")

conn = sqlite3.connect('users.db')
c = conn.cursor()

c.execute("SELECT * FROM users WHERE telegram_id = ?", (telegram_id,))
user = c.fetchone()

if not user:
    print("❌ User not found. Tell them to send /start to the bot first.")
    conn.close()
    exit()

paid_until = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d %H:%M:%S")
c.execute("UPDATE users SET paid = 1, paid_until = ? WHERE telegram_id = ?", 
          (paid_until, telegram_id))
conn.commit()
conn.close()

print("=" * 40)
print(f"✅ User {telegram_id} activated!")
print(f"✅ Paid until: {paid_until}")
print(f"✅ Unlimited posts unlocked.")
print("=" * 40)
