from telegram import (
    InlineKeyboardButton, InlineKeyboardMarkup, 
    ReplyKeyboardMarkup, KeyboardButton, Update
)
from telegram.ext import (
    Application, CommandHandler, CallbackContext,
    CallbackQueryHandler, MessageHandler, filters,
    ContextTypes
)
import logging
import sqlite3
import os
from datetime import datetime, time, timedelta
import random
from dotenv import load_dotenv

load_dotenv()
API_TOKEN = os.getenv("TELEGRAM_API_TOKEN")

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Database setup
conn = sqlite3.connect('church_bot.db', check_same_thread=False)
cursor = conn.cursor()

# Create tables
cursor.execute('''
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    first_name TEXT,
    last_name TEXT,
    phone TEXT,
    dob TEXT,
    marital TEXT,
    gender TEXT,
    email TEXT,
    address TEXT,
    occupation TEXT,
    registration_date DATETIME
)''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS prayer_requests (
    request_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    request TEXT,
    timestamp DATETIME
)''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS attendance (
    attendance_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    attendance_date DATE,
    status TEXT CHECK(status IN ('Yes', 'No'))
)''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS bible_study_progress (
    user_id INTEGER PRIMARY KEY,
    last_lesson INTEGER,
    completed_lessons TEXT
)''')
conn.commit()

# Persistent menu keyboard
def get_menu_keyboard():
    return ReplyKeyboardMarkup(
        [[KeyboardButton("📜 Menu")]],
        resize_keyboard=True,
        is_persistent=True
    )

# Bible study materials
BIBLE_LESSONS = [
    {
        'title': 'Lesson 1: The Creation',
        'content': 'Genesis 1:1-31 - In the beginning God created the heavens and the earth...',
        'questions': ['What did God create on the first day?', 'What was the final act of creation?']
    },
    {
        'title': 'Lesson 2: The Fall of Man',
        'content': 'Genesis 3:1-24 - The serpent deceives Eve...',
        'questions': ['What fruit did Adam and Eve eat?', 'What were the consequences of their action?']
    }
]

# Daily Bible verses
BIBLE_VERSES = [
    "John 3:16 - For God so loved the world...",
    "Philippians 4:13 - I can do all things through Christ...",
    "Psalm 23:1 - The Lord is my shepherd..."
]

async def start(update: Update, context: CallbackContext):
    user = update.effective_user
    cursor.execute('SELECT first_name FROM users WHERE user_id = ?', (user.id,))
    result = cursor.fetchone()

    if result:
        first_name = result[0]
        await update.message.reply_text(
            f"Welcome back, {first_name}! Please click on the menu to access the church services.",
            reply_markup=get_menu_keyboard()
        )
        await show_main_menu(update, context)
    else:
        await update.message.reply_text(
            "📖 Welcome to Reconciliation Church Of God!\n\n"
            "This AI Chat Bot will help you stay connected with our church community.\n"
            "Let's start with your registration.",
            reply_markup=get_menu_keyboard()
        )
        await update.message.reply_text("Please enter your first name:")
        context.user_data['registration'] = {'step': 'first_name'}

async def show_main_menu(update: Update, context: CallbackContext):
    user = update.effective_user
    cursor.execute('SELECT user_id FROM users WHERE user_id = ?', (user.id,))
    result = cursor.fetchone()

    if result:
        menu_text = (
            "📜 Main Menu:\n\n"
            "1. 📖 Bible Study\n"
            "2. 🙏 Prayer Requests\n"
            "3. 💵 Donations\n"
            "4. 📅 Attendance\n"
            "5. 🎥 Service Videos\n"
            "6. 📚 Bible Lessons\n"
        )
        buttons = [
            [InlineKeyboardButton("📖 Bible Study", callback_data='bible')],
            [InlineKeyboardButton("🙏 Prayer Requests", callback_data='prayer')],
            [InlineKeyboardButton("💵 Donations", callback_data='donate')],
            [InlineKeyboardButton("📅 Attendance", callback_data='attendance')],
            [InlineKeyboardButton("🎥 Service Videos", callback_data='service_videos')],
            [InlineKeyboardButton("📚 Bible Lessons", callback_data='bible_lessons')]
        ]
    else:
        menu_text = (
            "📜 Main Menu:\n\n"
            "1. 📖 Bible Study\n"
            "2. 🙏 Prayer Requests\n"
            "3. 💵 Donations\n"
            "4. 📅 Attendance\n"
            "5. 🎥 Service Videos\n"
            "6. 📚 Bible Lessons\n"
            "7. 📝 Register\n"
        )
        buttons = [
            [InlineKeyboardButton("📖 Bible Study", callback_data='bible')],
            [InlineKeyboardButton("🙏 Prayer Requests", callback_data='prayer')],
            [InlineKeyboardButton("💵 Donations", callback_data='donate')],
            [InlineKeyboardButton("📅 Attendance", callback_data='attendance')],
            [InlineKeyboardButton("🎥 Service Videos", callback_data='service_videos')],
            [InlineKeyboardButton("📚 Bible Lessons", callback_data='bible_lessons')],
            [InlineKeyboardButton("📝 Register", callback_data='register')]
        ]

    await update.message.reply_text(
        menu_text,
        reply_markup=InlineKeyboardMarkup(buttons)
    )

async def handle_registration(update: Update, context: CallbackContext):
    text = update.message.text
    user_data = context.user_data.get('registration', {})
    step = user_data.get('step')

    if step == 'first_name':
        context.user_data['registration'] = {
            'step': 'last_name',
            'first_name': text
        }
        await update.message.reply_text("Please enter your last name:")
    
    elif step == 'last_name':
        context.user_data['registration']['last_name'] = text
        context.user_data['registration']['step'] = 'phone'
        await update.message.reply_text("Please enter your phone number:")

    elif step == 'phone':
        context.user_data['registration']['phone'] = text
        context.user_data['registration']['step'] = 'dob'
        await update.message.reply_text("Please enter your Day and Month of birth DD-MM:")

    elif step == 'dob':
        context.user_data['registration']['dob']= text
        context.user_data['registration']['step']= 'marital'
        await update.message.reply_text("Please enter your marital status:")

    elif step == 'marital':
        context.user_data['registration']['marital']= text
        context.user_data['registration'] ['step']= 'gender'
        await update.message.reply_text("Please enter your Gender Male/Female:")

    elif step == 'gender':
        context.user_data['registration']['gender']= text
        context.user_data['registration']['step']= 'email'
        await update.message.reply_text("Please enter your email address:")

    elif step == 'email':
        context.user_data['registration']['email']= text
        context.user_data['registration']['step']= 'address'
        await update.message.reply_text("Please enter your address:")

    elif step == 'address':
        context.user_data['registration']['address']= text
        context.user_data['registration']['step']= 'occupation'
        await update.message.reply_text("Please enter your occupation:")
    
    elif step == 'occupation':
        context.user_data['registration']['occupation']= text
        context.user_data['registration']['step']= 'complete'
        try:
            reg = context.user_data['registration']
            cursor.execute('''
                INSERT INTO users (user_id, first_name, last_name, phone, dob, marital, gender, email, address, occupation, registration_date)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                (
                    update.effective_user.id,
                    reg['first_name'],
                    reg['last_name'],
                    reg['phone'],
                    reg['dob'],
                    reg['marital'],
                    reg['gender'],
                    reg['email'],
                    reg['address'],
                    reg['occupation'],
                    datetime.now()
                )
            )
            conn.commit()
            
            # Send welcome video
            try:
                await update.message.reply_video(
                    video=open('welcome_video.mp4', 'rb'),
                    caption="🎉 Welcome to our church family!",
                    reply_markup=get_menu_keyboard()
                )
            except Exception as e:
                logger.error(f"Video error: {e}")
                await update.message.reply_text(
                    "Welcome to our church family!",
                    reply_markup=get_menu_keyboard()
                )

            await update.message.reply_text(
                f"Thanks for Joining Us!, {reg['first_name']}! Kindly click on the Menu button to access the church services.",
                reply_markup=get_menu_keyboard()
            )
            context.user_data.clear()

        except Exception as e:
            logger.error(f"Registration error: {e}")
            await update.message.reply_text(
                "Registration failed. Please try again.",
                reply_markup=get_menu_keyboard()
            )

async def handle_prayer_request(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    await update.message.reply_text("✝️ Please type your prayer request:")
    context.user_data['request'] = True

async def save_prayer_request(update: Update, context: CallbackContext):
    if 'request' in context.user_data:
        try:
            cursor.execute('''
                INSERT INTO prayer_requests (user_id, request, timestamp) 
                VALUES (?, ?, ?)
            ''', (update.effective_user.id, update.message.text, datetime.now()))
            conn.commit()
            await update.message.reply_text(
                "🙏 Your prayer request has been submitted successfully. We will pray for you!",
                reply_markup=get_menu_keyboard()
            )
        except Exception as e:
            logger.error(f"Prayer request error: {e}")
            await update.message.reply_text(
                "Failed to save request. Please try again.",
                reply_markup=get_menu_keyboard()
            )
        context.user_data.pop('expecting_prayer', None)
    else:
        await update.message.reply_text(
            "Please use the menu to select an option.",
            reply_markup=get_menu_keyboard()
        )

async def handle_donations(update: Update, context: CallbackContext):
    await update.callback_query.answer()
    await update.callback_query.edit_message_text(
        "💵 Church Account Details:\n\n"
        "Bank: FCMB\n"
        "Account Name: Reconciliation Church\n"
        "Account Number: 0751609016\n\n"
        "Thank you for your generous giving!",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("Confirm Payment", callback_data='confirm_payment')]
        ])
    )

async def handle_bible_study(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    cursor.execute('SELECT last_lesson FROM bible_study_progress WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()
    lesson_number = result[0] + 1 if result else 0

    if lesson_number >= len(BIBLE_LESSONS):
        await update.callback_query.edit_message_text(
            "🎉 You've completed all available lessons! Check back later for new content.",
            reply_markup=get_menu_keyboard()
        )
        return

    lesson = BIBLE_LESSONS[lesson_number]
    await update.callback_query.edit_message_text(
        f"📖 {lesson['title']}\n\n{lesson['content']}",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("I've finished reading", callback_data=f'lesson_done_{lesson_number}')]
        ])
    )

async def handle_lesson_completion(update: Update, context: CallbackContext):
    lesson_number = int(update.callback_query.data.split('_')[-1])
    user_id = update.effective_user.id
    lesson = BIBLE_LESSONS[lesson_number]

    # Store lesson progress
    cursor.execute('''
        INSERT OR REPLACE INTO bible_study_progress 
        VALUES (?, ?, ?)
    ''', (user_id, lesson_number, str(lesson_number)))
    conn.commit()

    # Ask questions
    context.user_data['bible_q'] = {
        'lesson': lesson_number,
        'questions': lesson['questions'],
        'current_q': 0
    }
    await ask_next_question(update, context)

async def ask_next_question(update: Update, context: CallbackContext):
    q_data = context.user_data['bible_q']
    question = q_data['questions'][q_data['current_q']]
    
    await update.callback_query.edit_message_text(
        f"❓ Question {q_data['current_q']+1}/{len(q_data['questions'])}:\n{question}",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("Next Question", callback_data='next_question')]
        ])
    )

async def send_daily_reminder(context: ContextTypes.DEFAULT_TYPE):
    cursor.execute('SELECT user_id FROM users')
    for user in cursor.fetchall():
        try:
            verse = random.choice(BIBLE_VERSES)
            await context.bot.send_message(
                chat_id=user[0],
                text=f"☀️ Good Morning!\n\nToday's Bible Verse:\n{verse}",
                reply_markup=get_menu_keyboard()
            )
        except Exception as e:
            logger.error(f"Morning reminder error: {e}")

async def send_evening_checkin(context: ContextTypes.DEFAULT_TYPE):
    cursor.execute('SELECT user_id FROM users')
    for user in cursor.fetchall():
        try:
            await context.bot.send_message(
                chat_id=user[0],
                text="🌙 Good Evening! How was your day?",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("😊 Great", callback_data='day_good'),
                     InlineKeyboardButton("😐 Okay", callback_data='day_ok'),
                     InlineKeyboardButton("😞 Tough", callback_data='day_bad')]
                ])
            )
        except Exception as e:
            logger.error(f"Evening checkin error: {e}")

async def send_event_reminder(context: CallbackContext):
    cursor.execute('SELECT user_id FROM users')
    users = cursor.fetchall()
    for user in users:
        try:
            await context.bot.send_message(
                chat_id=user[0],
                text="🔔 Reminder: Don't forget the Prayer Meeting coming up soon this evening!"
            )
        except Exception as e:
            logger.error(f"Failed to send reminder to user {user[0]}: {e}")

async def send_checkup_message(context: CallbackContext):
    cursor.execute('SELECT user_id FROM users')
    users = cursor.fetchall()
    for user in users:
        try:
            await context.bot.send_message(
                chat_id=user[0],
                text="🔔 How is your day going? Here is a video to uplift your spirits!"
            )
            await context.bot.send_video(
                chat_id=user[0],
                video=open('checkingup.mp4', 'rb'),
                caption="Enjoy this uplifting video!"
            )
        except Exception as e:
            logger.error(f"Failed to send checkup message to user {user[0]}: {e}")

async def show_registered_members(update: Update, context: CallbackContext):
    # Check if the user is an admin (you can customize this check as needed)
    admin_user_id = 7885357096  # Replace with the actual admin user ID
    if update.effective_user.id != admin_user_id:
        await update.message.reply_text("You are not authorized to view this information.")
        return

    cursor.execute('SELECT first_name, last_name, phone, email, address FROM users')
    users = cursor.fetchall()
    if not users:
        await update.message.reply_text("No registered members found.")
        return

    message = "📋 Registered Members:\n\n"
    for user in users:
        message += (
            f"Name: {user[0]} {user[1]}\n"
            f"Phone: {user[2]}\n"
            f"Email: {user[3]}\n"
            f"Address: {user[4]}\n"
        )

    await update.message.reply_text(message)

def main():
    API_TOKEN = "8104104636:AAE3FdNpxfmo0Uz9nvt1jgvb4tjlE1GL6oA"
    app = Application.builder().token(API_TOKEN).build()

    # Handlers
    app.add_handler(CommandHandler('start', start))
    app.add_handler(CommandHandler('show_members', show_registered_members))
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex(r'^📜 Menu$'), show_main_menu))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_registration))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, save_prayer_request))
    
    # Callback handlers
    app.add_handler(CallbackQueryHandler(handle_prayer_request, pattern='^prayer$'))
    app.add_handler(CallbackQueryHandler(handle_donations, pattern='^donate$'))
    app.add_handler(CallbackQueryHandler(handle_bible_study, pattern='^bible$'))
    app.add_handler(CallbackQueryHandler(handle_lesson_completion, pattern='^lesson_done_'))
    app.add_handler(CallbackQueryHandler(ask_next_question, pattern='^next_question$'))

    # Schedule daily reminders
    job_queue = app.job_queue
    job_queue.run_daily(send_daily_reminder, time=time(hour=7), days=tuple(range(7)))
    job_queue.run_daily(send_evening_checkin, time=time(hour=19), days=tuple(range(7)))
    job_queue.run_repeating(send_event_reminder, interval=60, first=0)
    job_queue.run_repeating(send_checkup_message, interval=300, first=0)  # Every 5 minutes

    # Error handling
    app.add_error_handler(lambda update, context: logger.error(context.error))

    app.run_polling()

if __name__ == '__main__':
    main()