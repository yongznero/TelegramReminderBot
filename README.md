# Telegram Reminder Bot - Quick Start

## What You Need
1. A Telegram account
2. Python 3.8+ installed on your computer
3. 5 minutes of your time

## Setup Steps

### 1. Get Your Bot Token
1. Open Telegram and search for `@BotFather`
2. Send `/newbot` and follow the instructions
3. Copy the token (looks like: `1234567890:ABCdef...`)

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure the Bot
1. Open `reminder_bot.py`
2. Replace `YOUR_BOT_TOKEN_HERE` with your actual token
3. Save the file

### 4. Run the Bot
```bash
python reminder_bot.py
```

### 5. Test It
1. Find your bot in Telegram
2. Send: "Remind me to test this in 1 minute"
3. Wait for the reminder!

## Example Commands
- "Remind me to buy milk in 2 hours"
- "Remind me to call mom tomorrow at 3pm"
- "Remind me about the meeting on Friday at 9am"
- `/list` - See all reminders
- `/cancel 1` - Cancel reminder #1

## Need Help?
See `telegram_reminder_bot_guide.md` for detailed instructions and troubleshooting.
