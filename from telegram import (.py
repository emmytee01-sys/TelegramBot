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
    await update.message.reply_text(
        "📖 Welcome to Reconciliation Church Of God!\n\n"
        "This AI will help you stay connected with our church community.\n"
        "Let's start with your registration.",
        reply_markup=get_menu_keyboard()
    )
    await update.message.reply_text("Please enter your first name:")
    context.user_data['registration'] = {'step': 'first_name'}

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
                f"Registration complete, {reg['first_name']}! Kindly click on the Menu button to access the church services.",
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
    await query.edit_message_text("✝️ Please type your prayer request:")
    context.user_data['expecting_prayer'] = True

async def save_prayer_request(update: Update, context: CallbackContext):
    try:
        cursor.execute('''
            INSERT INTO prayer_requests VALUES (NULL,?,?,?)''',
            (update.effective_user.id, update.message.text, datetime.now())
        )
        conn.commit()
        await update.message.reply_text(
            "🙏 Your prayer request has been received. We will pray for you!",
            reply_markup=get_menu_keyboard()
        )
    except Exception as e:
        logger.error(f"Prayer request error: {e}")
        await update.message.reply_text(
            "Failed to save request. Please try again.",
            reply_markup=get_menu_keyboard()
        )
    context.user_data.pop('expecting_prayer', None)

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

def main():
    API_TOKEN = os.getenv("TELEGRAM_API_TOKEN")
    app = Application.builder().token(API_TOKEN).build()

    # Handlers
    app.add_handler(CommandHandler('start', start))
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

    # Error handling
    app.add_error_handler(lambda update, context: logger.error(context.error))

    app.run_polling()

if __name__ == '__main__':
    main()