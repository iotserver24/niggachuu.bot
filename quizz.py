import asyncio
import logging
import time
import random
from telegram.constants import ParseMode, ChatAction
from telegram import Update, Poll, InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackContext, ConversationHandler, PollAnswerHandler, filters, CallbackQueryHandler

# Use your actual bot token here
bot_token = '7518438812:AAF29rspjnbm48FQMZXJBCTOL1U5HOUJC-4'

# Quiz states
(ASK_NAME, ASK_QUESTION_TYPE, ASK_QUESTION, ASK_OPTIONS, ASK_ANSWER, ASK_TIME_GAP, ADD_MORE_QUESTIONS, ASK_START_TIMER) = range(8)

# Quiz management
quizzes = {}  # Store quizzes globally for all users, track their data
quiz_participants = {}  # Track group participants and their answers/timing
quiz_results = {}  # Store quiz results for the creator
user_quizzes = {}  # Store all quizzes created by a user

# Setup logging to handle errors
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Start command: Personalized greetings and keyboard commands
async def start(update: Update, context: CallbackContext):
    user = update.message.from_user

    # Display typing action before responding
    await context.bot.send_chat_action(chat_id=user.id, action=ChatAction.TYPING)
    await asyncio.sleep(1)  # Simulate typing time

    # Keyboard buttons for commands
    keyboard = [
        [KeyboardButton("/createquiz"), KeyboardButton("/myquizzes")],
        [KeyboardButton("/startquiz"), KeyboardButton("/pausequiz")],
        [KeyboardButton("/resumequiz"), KeyboardButton("/deletequiz")],
        [KeyboardButton("/results")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    await context.bot.send_message(chat_id=user.id,
                                   text=f"👋 Hello, *{user.first_name}*! Welcome to the Quiz Bot! 🤖\n"
                                        "Use the commands below to create and manage your quizzes.",
                                   parse_mode=ParseMode.MARKDOWN,
                                   reply_markup=reply_markup)


# Creating a new quiz, first step is to ask for the quiz name
async def create_quiz(update: Update, context: CallbackContext):
    await update.message.reply_text("📝 Please enter a name for your quiz:")
    return ASK_NAME


# Ask for the quiz name
async def ask_name(update: Update, context: CallbackContext):
    quiz_name = update.message.text
    user_id = update.message.from_user.id  # Get the ID of the quiz creator
    context.user_data['quiz_name'] = quiz_name
    context.user_data['questions'] = []  # Initialize empty question list
    context.user_data['creator'] = user_id  # Store the creator's ID

    # Store the quiz in the global list of user-created quizzes
    if user_id not in user_quizzes:
        user_quizzes[user_id] = []
    user_quizzes[user_id].append(quiz_name)

    # Ask for time gap between questions
    await update.message.reply_text("⏳ How many seconds should the gap between each question be?")
    return ASK_TIME_GAP


# Handle time gap input and then ask question type (single or multiple)
async def ask_time_gap(update: Update, context: CallbackContext):
    try:
        if update.message.text.isdigit():
            time_gap = int(update.message.text)
            context.user_data['time_gap'] = time_gap  # Store the time gap between questions

            # Buttons for single or multiple question quiz
            keyboard = [[InlineKeyboardButton("Single Question", callback_data='single')],
                        [InlineKeyboardButton("Multiple Questions", callback_data='multiple')]]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await update.message.reply_text("📊 Do you want to create a 'Single Question' or 'Multiple Questions' quiz?",
                                            reply_markup=reply_markup)
            return ASK_QUESTION_TYPE
        else:
            await update.message.reply_text("❌ Invalid input. Please enter a valid number of seconds.")
            return ASK_TIME_GAP
    except Exception as e:
        logger.error(f"Error in ask_time_gap handler: {e}")
        await update.message.reply_text("An error occurred. Please try again.")
        return ASK_TIME_GAP


# Handle question type via button callback
async def ask_question_type(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()

    answer = query.data
    if answer == 'single':
        context.user_data['quiz_type'] = 'single'
        await query.edit_message_text("🎯 You've chosen to create a 'Single Question' quiz.\nPlease send the question.")
        return ASK_QUESTION
    elif answer == 'multiple':
        context.user_data['quiz_type'] = 'multiple'
        await query.edit_message_text("🔢 You've chosen to create a 'Multiple Questions' quiz.\nPlease send the first question.")
        return ASK_QUESTION


# Ask for the question
async def ask_question(update: Update, context: CallbackContext):
    context.user_data['current_question'] = update.message.text
    await update.message.reply_text("🤔 Got it! Now, send the options for this question (comma-separated).")
    return ASK_OPTIONS


# Ask for the options
async def ask_options(update: Update, context: CallbackContext):
    options = update.message.text.split(',')
    context.user_data['current_options'] = options
    await update.message.reply_text("✅ Now, please send the correct answer number (e.g., 1 for the first option).")
    return ASK_ANSWER


# Ask for the correct answer with validation
async def ask_answer(update: Update, context: CallbackContext):
    try:
        if update.message.text.isdigit():
            correct_answer = int(update.message.text)
            context.user_data['correct_answer'] = correct_answer - 1  # 0-based index

            # Save the question to the list
            context.user_data['questions'].append({
                'question': context.user_data['current_question'],
                'options': context.user_data['current_options'],
                'correct_answer': context.user_data['correct_answer']
            })

            # If it's a multiple-question quiz, ask whether to add more questions
            if context.user_data['quiz_type'] == 'multiple':
                keyboard = [[InlineKeyboardButton("➕ Add More Questions", callback_data='add_more')],
                            [InlineKeyboardButton("✔ Complete Quiz", callback_data='complete_quiz')]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await update.message.reply_text("Do you want to add more questions or complete the quiz?",
                                                reply_markup=reply_markup)
                return ADD_MORE_QUESTIONS
            else:
                await finalize_quiz(update, context)
                return ConversationHandler.END
        else:
            await update.message.reply_text("❌ Invalid input. Please enter a number for the correct answer.")
            return ASK_ANSWER
    except Exception as e:
        logger.error(f"Error in ask_answer handler: {e}")
        await update.message.reply_text("An error occurred. Please try again.")
        return ASK_ANSWER


# Handling add more or complete quiz options
async def add_more_questions(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()

    if query.data == 'add_more':
        await query.edit_message_text("🔢 Please send the next question.")
        return ASK_QUESTION
    elif query.data == 'complete_quiz':
        await finalize_quiz(update, context)
        return ConversationHandler.END


# Finalize the quiz and save it globally
async def finalize_quiz(update: Update, context: CallbackContext):
    user_id = context.user_data['creator']
    quiz_name = context.user_data['quiz_name']
    questions = context.user_data['questions']
    time_gap = context.user_data.get('time_gap', 0)  # Default to 0 if no time gap

    # Save the quiz globally under its name
    quizzes[quiz_name] = {
        'creator': user_id,
        'questions': questions,
        'status': 'ready',
        'time_gap': time_gap
    }

    await update.message.reply_text(f"🚀 You have completed the quiz! You can start it with /startquiz {quiz_name}.")
    return ConversationHandler.END


# Start a specific quiz by quiz name, send questions as polls with time gaps and countdown
async def start_quiz(update: Update, context: CallbackContext):
    args = context.args
    user_id = update.message.from_user.id

    if not args:
        await update.message.reply_text("❌ You need to provide a quiz name. Usage: /startquiz <quiz_name>")
        return

    quiz_name = ' '.join(args)
    if quiz_name not in quizzes:
        await update.message.reply_text("❌ Quiz not found. Please provide a valid quiz name.")
        return

    quiz = quizzes[quiz_name]
    if user_id != quiz['creator']:
        await update.message.reply_text("❌ Only the quiz creator can start the quiz.")
        return

    # Ask for the countdown time before the quiz starts
    await update.message.reply_text("⏳ How many minutes do you want to wait before starting the quiz?")
    context.user_data['quiz_name'] = quiz_name  # Store the quiz name for later use
    return ASK_START_TIMER


# Handle the start timer input
async def ask_start_timer(update: Update, context: CallbackContext):
    try:
        if update.message.text.isdigit():
            start_timer = int(update.message.text)
            quiz_name = context.user_data['quiz_name']
            quiz = quizzes[quiz_name]

            # Countdown timer before starting the quiz
            await update.message.reply_text(f"⏳ The quiz will start in {start_timer} minutes!")
            await asyncio.sleep(start_timer * 60)  # Wait for the specified number of minutes

            # Start the quiz after the countdown
            await update.message.reply_text(f"🚀 Starting quiz '{quiz_name}'!")

            # Send the questions one by one with the specified time gap
            for idx, question_data in enumerate(quiz['questions']):
                # Countdown before each question
                for countdown in range(3, 0, -1):
                    await update.message.reply_text(f"{countdown}...")
                    await asyncio.sleep(1)  # 1-second delay between countdown

                # Send the poll question
                await context.bot.send_poll(
                    chat_id=update.effective_chat.id,
                    question=question_data['question'],
                    options=question_data['options'],
                    is_anonymous=True,  # Keep the answers anonymous during the quiz
                    type=Poll.QUIZ,
                    correct_option_id=question_data['correct_answer']
                )

                # Wait for the time gap between questions
                time_gap = quiz.get('time_gap', 0)
                if time_gap > 0 and idx < len(quiz['questions']) - 1:  # Don't wait after the last question
                    await update.message.reply_text(f"⏳ Next question in {time_gap} seconds...")
                    await asyncio.sleep(time_gap)
        else:
            await update.message.reply_text("❌ Invalid input. Please enter a valid number of minutes.")
            return ASK_START_TIMER
    except Exception as e:
        logger.error(f"Error in ask_start_timer handler: {e}")
        await update.message.reply_text("An error occurred. Please try again.")
        return ASK_START_TIMER


# Handle poll answers, track answer time, and store results
async def handle_poll_answer(update: Update, context: CallbackContext):
    answer = update.poll_answer
    quiz_name = None

    # Find which quiz the poll belongs to
    for qname, data in quizzes.items():
        if data.get('poll_message_id') == answer.poll_id:
            quiz_name = qname
            break

    if not quiz_name:
        return

    quiz = quizzes[quiz_name]
    user_id = answer.user.id
    answer_time = time.time() - quiz['start_time']  # Calculate the time taken to answer

    # Store the participant's answer and time
    if user_id not in quiz_participants:
        quiz_participants[user_id] = []
    quiz_participants[user_id].append({
        'quiz_name': quiz_name,
        'answer': answer.option_ids[0],  # First answer given
        'time_taken': answer_time
    })

    # Log the answer and the time taken
    logger.info(f"User {user_id} answered {answer.option_ids[0]} in {answer_time} seconds.")


# End the quiz and send results privately to the creator
async def end_quiz(update: Update, context: CallbackContext, quiz_name: str):
    quiz = quizzes[quiz_name]
    creator_id = quiz['creator']

    # Calculate results (based on correct answers and time taken)
    results = []
    for user_id, answers in quiz_participants.items():
        correct_answers = sum(1 for answer in answers if answer['quiz_name'] == quiz_name and answer['answer'] == quiz['questions'][0]['correct_answer'])
        if correct_answers > 0:
            results.append((user_id, correct_answers))

    # Sort the results by the number of correct answers
    results.sort(key=lambda x: x[1], reverse=True)

    # Prepare the results message
    result_message = f"📊 Results for quiz '{quiz_name}':\n"
    for i, (user_id, correct_answers) in enumerate(results, start=1):
        user = await context.bot.get_chat(user_id)  # Get the username of the user
        result_message += f"{i}. {user.username or user.first_name}: {correct_answers} correct answers\n"

    # Send the results only to the creator in a private message
    await context.bot.send_message(chat_id=creator_id, text=result_message)

    # Clean up quiz data
    del quiz_participants[creator_id]


# Command to choose a random user in the group (must be an admin)
async def random_winner(update: Update, context: CallbackContext):
    chat = update.effective_chat
    user = update.effective_user

    # Check if the command is used in a group
    if chat.type != "group" and chat.type != "supergroup":
        await update.message.reply_text("❌ This command can only be used in groups.")
        return

    # Check if the user is an admin
    member_status = await context.bot.get_chat_member(chat_id=chat.id, user_id=user.id)
    if not member_status.status in ['administrator', 'creator']:
        await update.message.reply_text("❌ Only admins can use this command.")
        return

    # Get all group members
    members = await context.bot.get_chat_administrators(chat.id)
    members_list = [member.user for member in members if not member.user.is_bot]

    if members_list:
        # Choose a random user
        winner = random.choice(members_list)
        await update.message.reply_text(f"🎉 The winner is {winner.first_name}! 🏆🎊")
    else:
        await update.message.reply_text("❌ No eligible users found in this group.")


# Main function to run the bot
def main():
    application = Application.builder().token(bot_token).build()

    # Conversation handler for creating a quiz
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("createquiz", create_quiz)],
        states={
            ASK_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_name)],
            ASK_QUESTION_TYPE: [CallbackQueryHandler(ask_question_type)],
            ASK_QUESTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_question)],
            ASK_OPTIONS: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_options)],
            ASK_ANSWER: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_answer)],
            ASK_TIME_GAP: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_time_gap)],
            ASK_START_TIMER: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_start_timer)],
            ADD_MORE_QUESTIONS: [CallbackQueryHandler(add_more_questions)]
        },
        fallbacks=[CommandHandler("cancel", lambda update, context: update.message.reply_text("Quiz creation canceled."))]
    )

    # Register handlers for additional commands
    application.add_handler(conv_handler)
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("myquizzes", my_quizzes))
    application.add_handler(CommandHandler("startquiz", start_quiz))
    application.add_handler(CommandHandler("deletequiz", delete_quiz))
    application.add_handler(CommandHandler("results", results))
    application.add_handler(CommandHandler("random", random_winner))
    application.add_handler(PollAnswerHandler(handle_poll_answer))

    # Start the bot
    application.run_polling()

if __name__ == '__main__':
    main()
