# TelegramBot
This repository contains the source code for the Telegram Bot. This bot helps the church community stay connected by providing various features such as Bible study, prayer requests, donations, attendance tracking, and more.

# Features
Bible Study: Access Bible lessons and answer questions.
Prayer Requests: Submit prayer requests and receive confirmation.
Donations: Information on how to donate to the church.
Attendance: Track attendance for church events.
Service Videos: Watch recorded church services.
Daily Reminders: Receive daily Bible verses and evening check-ins.
Event Reminders: Get reminders for upcoming church events.

# Setup
Clone the repository:git clone https://github.com/emmytee01-sys/TelegramBot.git
cd TelegramBot

Create a virtual environment: python3 -m venv venv
source venv/bin/activate  # On Windows use `venv\Scripts\activate`

Install dependencies: pip install -r requirements.txt

Set up environment variables: Create a .env file in the root directory with the following content:
API_TOKEN=your-telegram-bot-token
DB_HOST=localhost
DB_USER=your-database-username
DB_PASS=your-database-password
DB_NAME=your-database-name

Run the bot:
python bot.py

# Usage
Start the bot: /start
Show main menu: 📜 Menu
Submit a prayer request: Click on "🙏 Prayer Requests" and type your request.
View registered members (Admin only): /show_members
Contributing
Contributions are welcome! Please fork the repository and submit a pull request with your changes.

# License
This project is licensed under the MIT License.
