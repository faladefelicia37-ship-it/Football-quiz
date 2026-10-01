import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
import os

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

# Get token from Railway environment variable
TOKEN = os.environ.get("TELEGRAM_TOKEN")

# --- Quiz Data (No Gambling, Pure Entertainment) ---
QUESTIONS = [
    {
        "question": "Which country won the 2018 FIFA World Cup?",
        "options": ["Germany", "Brazil", "France", "Croatia"],
        "answer": "France"
    },
    {
        "question": "Who has won the most Ballon d'Or awards?",
        "options": ["Cristiano Ronaldo", "Lionel Messi", "Michel Platini", "Johan Cruyff"],
        "answer": "Lionel Messi"
    },
    {
        "question": "How many players are on the pitch per team in a standard football match?",
        "options": ["9", "10", "11", "12"],
        "answer": "11"
    }
]

# In-memory storage (resets on deploy)
user_data = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when /start is issued."""
    user_id = update.effective_user.id
    user_data[user_id] = {"score": 0, "index": 0}
    
    await update.message.reply_text(
        "Welcome to the Football Quiz! ⚽\n"
        "Let's test your knowledge.\n"
        "Use /help for instructions."
    )
    await ask_question(update, context)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a help message."""
    await update.message.reply_text(
        "This is a simple trivia game. No real prizes or betting involved.\n"
        "Commands:\n"
        "/start - Begin the quiz\n"
        "/score - Check your current score\n"
        "/help - Show this message"
    )

async def score_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Check the user's current score."""
    user_id = update.effective_user.id
    score = user_data.get(user_id, {}).get("score", 0)
    await update.message.reply_text(f"Your current score is: {score}")

async def ask_question(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send the current question with inline buttons."""
    user_id = update.effective_user.id
    data = user_data.get(user_id)
    
    if not data:
        await update.message.reply_text("Please type /start to begin.")
        return

    idx = data["index"]
    if idx >= len(QUESTIONS):
        await update.message.reply_text(f"Quiz complete! Your final score: {data['score']}")
        return

    q = QUESTIONS[idx]
    keyboard = []
    for option in q["options"]:
        keyboard.append([InlineKeyboardButton(option, callback_data=f"ans_{option}")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Use context.bot.send_message if the update comes from a callback
    if update.callback_query:
        await update.callback_query.edit_message_text(
            text=q["question"], reply_markup=reply_markup
        )
    else:
        await update.message.reply_text(
            text=q["question"], reply_markup=reply_markup
        )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle button presses."""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    data = user_data.get(user_id)
    
    if not data:
        await query.edit_message_text("Session expired. Please type /start.")
        return

    selected = query.data.replace("ans_", "")
    current_q = QUESTIONS[data["index"]]
    
    if selected == current_q["answer"]:
        data["score"] += 1
        await query.edit_message_text(f"Correct! ✅ Score: {data['score']}")
    else:
        await query.edit_message_text(f"Wrong. ❌ The answer was: {current_q['answer']}")
    
    data["index"] += 1
    
    # Wait a moment then ask next question
    # Using a simple inline wait or just immediate edit
    if data["index"] < len(QUESTIONS):
        # We need to ask next question. Since we can't edit the same message easily after a delay without a job, 
        # we can send a new message or edit immediately.
        # For simplicity, we edit immediately to the next question.
        q = QUESTIONS[data["index"]]
        keyboard = [[InlineKeyboardButton(opt, callback_data=f"ans_{opt}")] for opt in q["options"]]
        await query.edit_message_text(
            text=f"Next Question:\n{q['question']}", 
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    else:
        await query.edit_message_text(f"Quiz Finished! Final Score: {data['score']}")
        # Reset for replay
        user_data[user_id] = {"score": 0, "index": 0}

def main() -> None:
    """Start the bot."""
    if not TOKEN:
        print("Error: TELEGRAM_TOKEN not set.")
        return

    application = Application.builder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("score", score_command))
    application.add_handler(CallbackQueryHandler(button_handler))

    # Run the bot until the user presses Ctrl-C
    print("Bot is starting...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
