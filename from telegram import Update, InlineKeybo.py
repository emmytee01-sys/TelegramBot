from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackContext, CallbackQueryHandler
import mysql.connector
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
import logging

# Logging configuration
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# MySQL connection
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="Damilare002!",
    database="detunsys_church_bot"
)
cursor = db.cursor()

# Bot start command
async def start(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    username = update.effective_user.username

    # Save user to the database if not already registered
    try:
        cursor.execute("INSERT INTO users (user_id, username) VALUES (%s, %s) ON DUPLICATE KEY UPDATE username=%s",
                       (user_id, username, username))
        db.commit()
    except Exception as e:
        logger.error(f"Error saving user: {e}")

    keyboard = [
        [InlineKeyboardButton("Attendance", callback_data='attendance')],
        [InlineKeyboardButton("Prayer Request", callback_data='prayer')],
        [InlineKeyboardButton("Event Reminders", callback_data='event')],
        [InlineKeyboardButton("Donations", callback_data='donate')],
        [InlineKeyboardButton("Daily Reminders", callback_data='reminder')],
        [InlineKeyboardButton("Bible Study", callback_data='bible')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "Welcome to the Reconciliation Church Of God AI Bot! Please choose an option:",
        reply_markup=reply_markup
    )

# Add event command
async def add_event(update: Update, context: CallbackContext):
    try:
        args = context.args
        if len(args) < 3:
            await update.message.reply_text("Usage: /add_event <event_name> <YYYY-MM-DD HH:MM> <message>")
            return

        event_name = args[0]
        event_time = args[1] + " " + args[2]
        message = " ".join(args[3:])

        cursor.execute("INSERT INTO event_reminders (event_name, event_time, message) VALUES (%s, %s, %s)",
                       (event_name, event_time, message))
        db.commit()

        await update.message.reply_text("Event added successfully!")
    except Exception as e:
        logger.error(f"Error adding event: {e}")
        await update.message.reply_text(f"Error: {e}")

# View events command
async def view_events(update: Update, context: CallbackContext):
    cursor.execute("SELECT event_name, event_time FROM event_reminders ORDER BY event_time ASC")
    events = cursor.fetchall()

    if events:
        event_list = "\n".join([f"{event_name} at {event_time}" for event_name, event_time in events])
        await update.message.reply_text(f"Upcoming Events:\n{event_list}")
    else:
        await update.message.reply_text("No upcoming events.")

# Event reminders
async def send_event_reminders(context: CallbackContext):
    now = datetime.now()
    cursor.execute("SELECT event_name, message FROM event_reminders WHERE event_time >= %s AND event_time <= %s",
                   (now, now.replace(hour=23, minute=59, second=59)))
    events = cursor.fetchall()

    if events:
        cursor.execute("SELECT user_id FROM users")
        users = cursor.fetchall()

        for event_name, message in events:
            for (user_id,) in users:
                try:
                    await context.bot.send_message(
                        chat_id=user_id,
                        text=f"📢 Reminder: {event_name}\n{message}"
                    )
                except Exception as e:
                    logger.error(f"Error sending message to {user_id}: {e}")

# Callback query handler
async def button(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()

    if query.data == 'attendance':
        await query.edit_message_text("Do you attend the service today? Reply with Yes or No.")
    elif query.data == 'prayer':
        await query.edit_message_text("Send your prayer request to us.")
    elif query.data == 'event':
        await view_events(update, context)
    elif query.data == 'donate':
        await query.edit_message_text("To make a donation, please send to BANK: FCMB ACCOUNT NAME: Reconciliation Church of God ACCOUNT NUMBER: 0751609016.")
    elif query.data == 'reminder':
        await query.edit_message_text("Daily Reminder: Remember to pray and stay strong in faith.")
    elif query.data == 'bible':
        await query.edit_message_text("Bible Study Lesson: Today's topic is 'Faith and Works'. Read James 2:14-26.")

# Scheduler
scheduler = BackgroundScheduler()
scheduler.add_job(send_event_reminders, 'cron', hour=8, args=[CallbackContext])
scheduler.start()

# Main function
def main():
    application = Application.builder().token("8104104636:AAE3FdNpxfmo0Uz9nvt1jgvb4tjlE1GL6oA").build()

    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('add_event', add_event))
    application.add_handler(CommandHandler('view_events', view_events))
    application.add_handler(CallbackQueryHandler(button))

    application.run_polling()

if __name__ == '__main__':
    main()
