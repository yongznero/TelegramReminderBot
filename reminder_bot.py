import logging
from datetime import datetime, timedelta
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import re
import json
import os
from dateutil import parser as date_parser

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# File to store reminders persistently
REMINDERS_FILE = 'reminders.json'

def load_reminders():
    """Load reminders from file"""
    if os.path.exists(REMINDERS_FILE):
        with open(REMINDERS_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_reminders(reminders):
    """Save reminders to file"""
    with open(REMINDERS_FILE, 'w') as f:
        json.dump(reminders, f, indent=2)

# Load existing reminders
reminders_db = load_reminders()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a message when the command /start is issued."""
    welcome_message = """
Welcome to Reminder Bot! 🔔

I can help you set reminders. Here's how to use me:

📝 *Examples:*
• "Remind me to buy milk in 2 hours"
• "Remind me to call mom tomorrow at 3pm"
• "Remind me about the meeting in 30 minutes"
• "Remind me to exercise on Friday at 6am"

⏰ *Time formats I understand:*
• Relative: "in 5 minutes", "in 2 hours", "in 3 days"
• Specific: "tomorrow at 3pm", "on Monday at 9am"
• Date and time: "on Jan 15 at 2pm", "2025-01-20 14:30"

📋 *Commands:*
/start - Show this help message
/list - Show all your active reminders
/cancel [number] - Cancel a reminder by its number

Just send me a message with your reminder and I'll take care of it!
    """
    await update.message.reply_text(welcome_message, parse_mode='Markdown')

async def list_reminders(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """List all active reminders for the user"""
    user_id = str(update.effective_user.id)
    
    if user_id not in reminders_db or not reminders_db[user_id]:
        await update.message.reply_text("You don't have any active reminders.")
        return
    
    message = "📋 *Your Active Reminders:*\n\n"
    for idx, reminder in enumerate(reminders_db[user_id], 1):
        remind_time = datetime.fromisoformat(reminder['time'])
        message += f"{idx}. {reminder['text']}\n"
        message += f"   ⏰ {remind_time.strftime('%Y-%m-%d %I:%M %p')}\n\n"
    
    await update.message.reply_text(message, parse_mode='Markdown')

async def cancel_reminder(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel a reminder by number"""
    user_id = str(update.effective_user.id)
    
    if not context.args:
        await update.message.reply_text("Please specify the reminder number to cancel.\nExample: /cancel 1")
        return
    
    try:
        reminder_num = int(context.args[0])
        if user_id in reminders_db and 0 < reminder_num <= len(reminders_db[user_id]):
            cancelled = reminders_db[user_id].pop(reminder_num - 1)
            save_reminders(reminders_db)
            await update.message.reply_text(f"✅ Cancelled reminder: {cancelled['text']}")
        else:
            await update.message.reply_text("Invalid reminder number. Use /list to see your reminders.")
    except ValueError:
        await update.message.reply_text("Please provide a valid number. Example: /cancel 1")

def parse_time(text):
    """Parse various time formats from the reminder text"""
    text_lower = text.lower()
    
    # Relative time patterns
    relative_patterns = [
        (r'in (\d+) min(?:ute)?s?', 'minutes'),
        (r'in (\d+) hour?s?', 'hours'),
        (r'in (\d+) day?s?', 'days'),
        (r'in (\d+) week?s?', 'weeks'),
    ]
    
    for pattern, unit in relative_patterns:
        match = re.search(pattern, text_lower)
        if match:
            amount = int(match.group(1))
            if unit == 'minutes':
                return datetime.now() + timedelta(minutes=amount)
            elif unit == 'hours':
                return datetime.now() + timedelta(hours=amount)
            elif unit == 'days':
                return datetime.now() + timedelta(days=amount)
            elif unit == 'weeks':
                return datetime.now() + timedelta(weeks=amount)
    
    # Tomorrow pattern
    if 'tomorrow' in text_lower:
        tomorrow = datetime.now() + timedelta(days=1)
        time_match = re.search(r'at (\d+(?::\d+)?\s*(?:am|pm)?)', text_lower)
        if time_match:
            time_str = time_match.group(1)
            try:
                time_obj = date_parser.parse(time_str)
                return tomorrow.replace(hour=time_obj.hour, minute=time_obj.minute, second=0, microsecond=0)
            except:
                return tomorrow.replace(hour=9, minute=0, second=0, microsecond=0)
        return tomorrow.replace(hour=9, minute=0, second=0, microsecond=0)
    
    # Day of week pattern
    days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
    for i, day in enumerate(days):
        if day in text_lower:
            today = datetime.now()
            days_ahead = (i - today.weekday() + 7) % 7
            if days_ahead == 0:
                days_ahead = 7
            target_date = today + timedelta(days=days_ahead)
            
            time_match = re.search(r'at (\d+(?::\d+)?\s*(?:am|pm)?)', text_lower)
            if time_match:
                time_str = time_match.group(1)
                try:
                    time_obj = date_parser.parse(time_str)
                    return target_date.replace(hour=time_obj.hour, minute=time_obj.minute, second=0, microsecond=0)
                except:
                    pass
            return target_date.replace(hour=9, minute=0, second=0, microsecond=0)
    
    # Try parsing as a full date/time
    try:
        # Look for patterns like "on Jan 15 at 2pm" or "2025-01-20 14:30"
        date_match = re.search(r'(?:on|at)\s+(.+)', text_lower)
        if date_match:
            date_str = date_match.group(1)
            return date_parser.parse(date_str, fuzzy=True)
    except:
        pass
    
    return None

async def send_reminder(context: ContextTypes.DEFAULT_TYPE):
    """Send the reminder message to the user"""
    job_data = context.job.data
    try:
        await context.bot.send_message(
            chat_id=job_data['chat_id'],
            text=f"🔔 *Reminder!*\n\n{job_data['reminder_text']}",
            parse_mode='Markdown'
        )
        
        # Remove from database
        user_id = str(job_data['user_id'])
        if user_id in reminders_db:
            reminders_db[user_id] = [r for r in reminders_db[user_id] 
                                     if r['text'] != job_data['reminder_text'] 
                                     or r['time'] != job_data['time']]
            save_reminders(reminders_db)
    except Exception as e:
        logger.error(f"Error sending reminder: {e}")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle incoming reminder messages"""
    text = update.message.text
    user_id = str(update.effective_user.id)
    chat_id = update.effective_chat.id
    
    # Parse the reminder time
    remind_time = parse_time(text)
    
    if not remind_time:
        await update.message.reply_text(
            "I couldn't understand when you want to be reminded. 🤔\n\n"
            "Try something like:\n"
            "• 'Remind me to buy milk in 2 hours'\n"
            "• 'Remind me to call mom tomorrow at 3pm'\n"
            "• 'Remind me about the meeting in 30 minutes'"
        )
        return
    
    # Check if time is in the past
    if remind_time <= datetime.now():
        await update.message.reply_text(
            "That time is in the past! ⏰\n"
            "Please specify a future time for your reminder."
        )
        return
    
    # Extract the reminder text (remove time-related phrases)
    reminder_text = re.sub(r'(?:remind me (?:to|about)\s+)', '', text, flags=re.IGNORECASE)
    reminder_text = re.sub(r'(?:in \d+ (?:minute|hour|day|week)s?)', '', reminder_text, flags=re.IGNORECASE)
    reminder_text = re.sub(r'(?:tomorrow|on \w+)\s*(?:at \d+(?::\d+)?\s*(?:am|pm)?)?', '', reminder_text, flags=re.IGNORECASE)
    reminder_text = reminder_text.strip()
    
    # Schedule the reminder
    job_data = {
        'chat_id': chat_id,
        'user_id': user_id,
        'reminder_text': reminder_text,
        'time': remind_time.isoformat()
    }
    
    context.job_queue.run_once(
        send_reminder,
        when=remind_time,
        data=job_data,
        name=f"{user_id}_{remind_time.isoformat()}"
    )
    
    # Store in database
    if user_id not in reminders_db:
        reminders_db[user_id] = []
    
    reminders_db[user_id].append({
        'text': reminder_text,
        'time': remind_time.isoformat()
    })
    save_reminders(reminders_db)
    
    # Confirm to user
    time_diff = remind_time - datetime.now()
    if time_diff.days > 0:
        time_str = f"in {time_diff.days} day(s)"
    elif time_diff.seconds >= 3600:
        time_str = f"in {time_diff.seconds // 3600} hour(s)"
    else:
        time_str = f"in {time_diff.seconds // 60} minute(s)"
    
    await update.message.reply_text(
        f"✅ Reminder set!\n\n"
        f"📝 {reminder_text}\n"
        f"⏰ {remind_time.strftime('%Y-%m-%d %I:%M %p')}\n"
        f"({time_str})"
    )

def main():
    """Start the bot"""
    # Get token from environment variable
    BOT_TOKEN = os.environ.get('BOT_TOKEN')
    
    if not BOT_TOKEN:
        raise ValueError("No BOT_TOKEN found! Please set it in Render environment variables.")
    
    # Create the Application
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Register handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("list", list_reminders))
    application.add_handler(CommandHandler("cancel", cancel_reminder))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Start the Bot
    logger.info("Bot is starting...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
