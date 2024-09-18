import asyncio
import logging
import random
import time  # Import time module to track timing
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup
from telegram.constants import ParseMode, ChatAction
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackContext, ConversationHandler, filters, CallbackQueryHandler

# Bot token
bot_token = '7518438812:AAF29rspjnbm48FQMZXJBCTOL1U5HOUJC-4'

# Quiz states
(ASK_NAME, ASK_QUESTION_TYPE, ASK_QUESTION, ASK_OPTIONS, ASK_ANSWER, ASK_TIME_GAP, ADD_MORE_QUESTIONS) = range(7)

# Global variables for managing quizzes and participants
quizzes = {}  # Stores quizzes
quiz_participants = {}  # Track participants' answers per quiz
user_quizzes = {}  # Store quizzes created by users
active_question = {}  # Stores the current active question for each quiz
question_results = {}  # Track question-specific results for all questions

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- START COMMAND AND MENU ---
async def start(update: Update, context: CallbackContext):
    user = update.message.from_user
    await context.bot.send_chat_action(chat_id=user.id, action=ChatAction.TYPING)
    await asyncio.sleep(1)

    keyboard = [
        [KeyboardButton("/createquiz"), KeyboardButton("/myquizzes")],
        [KeyboardButton("/startquiz"), KeyboardButton("/pausequiz")],
        [KeyboardButton("/resumequiz"), KeyboardButton("/deletequiz")],
        [KeyboardButton("/results"), KeyboardButton("/random")],
        [KeyboardButton("/allcommands")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    await context.bot.send_message(chat_id=user.id,
                                   text=f"👋 Hello, *{user.first_name}*! Welcome to the Quiz Bot! 🤖",
                                   parse_mode=ParseMode.MARKDOWN,
                                   reply_markup=reply_markup)

# --- ALL COMMANDS FUNCTION ---
async def all_commands(update: Update, context: CallbackContext):
    commands = (
        "/start - Start the bot\n"
        "/createquiz - Create a new quiz\n"
        "/myquizzes - View quizzes you’ve created\n"
        "/startquiz <quiz_name> - Start a quiz\n"
        "/deletequiz <quiz_name> - Delete a quiz\n"
        "/pausequiz <quiz_name> - Pause a quiz\n"
        "/resumequiz <quiz_name> - Resume a paused quiz\n"
        "/results <quiz_name> - View quiz results\n"
        "/random - Choose a random member from the group\n"
        "/allcommands - Show all available commands"
    )
    await update.message.reply_text(f"📋 Here are all the available commands:\n\n{commands}")

# --- MY QUIZZES FUNCTION ---
async def my_quizzes(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    user_quiz_list = user_quizzes.get(user_id, [])

    if user_quiz_list:
        await update.message.reply_text(f"📋 Here are your quizzes:\n" + "\n".join(user_quiz_list))
    else:
        await update.message.reply_text("❌ You haven't created any quizzes yet.")

# --- QUIZ CREATION HANDLERS ---
async def create_quiz(update: Update, context: CallbackContext):
    await update.message.reply_text("📝 Please enter a name for your quiz:")
    return ASK_NAME

async def ask_name(update: Update, context: CallbackContext):
    quiz_name = update.message.text
    user_id = update.message.from_user.id
    context.user_data['quiz_name'] = quiz_name
    context.user_data['questions'] = []
    context.user_data['creator'] = user_id

    if user_id not in user_quizzes:
        user_quizzes[user_id] = []
    user_quizzes[user_id].append(quiz_name)

    await update.message.reply_text("⏳ How many seconds should the gap between each question be?")
    return ASK_TIME_GAP

async def ask_time_gap(update: Update, context: CallbackContext):
    try:
        if update.message.text.isdigit():
            time_gap = int(update.message.text)
            context.user_data['time_gap'] = time_gap

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

# --- QUESTION AND ANSWER HANDLERS ---
async def ask_question(update: Update, context: CallbackContext):
    context.user_data['current_question'] = update.message.text
    await update.message.reply_text("🤔 Got it! Now, send the options for this question (comma-separated).")
    return ASK_OPTIONS

async def ask_options(update: Update, context: CallbackContext):
    options = update.message.text.split(',')
    context.user_data['current_options'] = options
    await update.message.reply_text("✅ Now, please send the correct answer number (e.g., 1 for the first option).")
    return ASK_ANSWER

async def ask_answer(update: Update, context: CallbackContext):
    try:
        if update.message.text.isdigit():
            correct_answer = int(update.message.text) - 1  # Correct answer in 0-based index
            context.user_data['correct_answer'] = correct_answer

            context.user_data['questions'].append({
                'question': context.user_data['current_question'],
                'options': context.user_data['current_options'],
                'correct_answer': context.user_data['correct_answer']
            })

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

# --- ADD MORE QUESTIONS HANDLER ---
async def add_more_questions(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()

    if query.data == 'add_more':
        await query.edit_message_text("🔢 Please send the next question.")
        return ASK_QUESTION
    elif query.data == 'complete_quiz':
        await finalize_quiz(update, context)
        await query.edit_message_text("✔ You have completed the quiz! You can start it now.")
        return ConversationHandler.END

# --- FINALIZE THE QUIZ ---
async def finalize_quiz(update: Update, context: CallbackContext):
    user_id = context.user_data['creator']
    quiz_name = context.user_data['quiz_name']
    questions = context.user_data['questions']
    time_gap = context.user_data.get('time_gap', 0)

    quizzes[quiz_name] = {
        'creator': user_id,
        'questions': questions,
        'status': 'ready',
        'time_gap': time_gap
    }

    await update.message.reply_text(f"🚀 You have completed the quiz! You can start it with /startquiz {quiz_name}.")
    return ConversationHandler.END

# --- START QUIZ WITH SIMPLE MESSAGE QUESTIONS ---
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

    await update.message.reply_text(f"🚀 Starting quiz '{quiz_name}'!")

    # Reset participants for the entire quiz
    if quiz_name not in question_results:
        question_results[quiz_name] = {}

    # Send the questions one by one as a message and handle answers with time gap
    for idx, question_data in enumerate(quiz['questions']):
        active_question[quiz_name] = {
            'question_index': idx,
            'correct_answer': question_data['correct_answer'],
            'start_time': time.time(),
            'participants': {}  # Track participants for each question
        }

        # Send the question as a simple message
        question_text = f"❓ *Question {idx + 1}:* {question_data['question']}\n" + \
                        "\n".join([f"{i + 1}. {opt}" for i, opt in enumerate(question_data['options'])])
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=question_text,
            parse_mode=ParseMode.MARKDOWN
        )

        # Wait for the time gap before the next question
        time_gap = quiz.get('time_gap', 0)
        if time_gap > 0 and idx < len(quiz['questions']) - 1:
            await asyncio.sleep(time_gap)

    # After sending all questions, automatically send results to the creator
    await send_results_to_creator(update, context, quiz_name)

# --- HANDLE TEXT ANSWERS ---
async def handle_text_answer(update: Update, context: CallbackContext):
    if not update.message or not update.message.text.isdigit():  # Ensure only numeric answers are handled
        return

    user = update.message.from_user
    user_id = user.id
    answer_text = update.message.text.strip()

    quiz_name = None

    # Find the active quiz
    for qname, data in active_question.items():
        if data:
            quiz_name = qname
            break

    if not quiz_name:
        return  # Ignore if there's no active question

    quiz_data = active_question[quiz_name]
    participants = quiz_data['participants']
    question_index = quiz_data['question_index']

    # Check if the user has already answered
    if user_id in participants:
        return  # Ignore further answers from the same user for this question

    # Validate if the answer is within the options
    answer = int(answer_text) - 1  # Convert to 0-based index
    correct_answer = quiz_data['correct_answer']

    # Check if the answer is correct
    if answer == correct_answer:
        time_taken = time.time() - quiz_data['start_time']
        participants[user_id] = {'correct': True, 'time_taken': time_taken}
    else:
        participants[user_id] = {'correct': False, 'time_taken': None}

    # Store the participant's result for this question in question_results
    if quiz_name not in question_results:
        question_results[quiz_name] = {}
    
    if question_index not in question_results[quiz_name]:
        question_results[quiz_name][question_index] = {}

    question_results[quiz_name][question_index][user_id] = {
        'correct': answer == correct_answer,
        'time_taken': time_taken if answer == correct_answer else None
    }

# --- SEND RESULTS TO CREATOR ---
async def send_results_to_creator(update: Update, context: CallbackContext, quiz_name: str):
    quiz = quizzes.get(quiz_name)
    creator_id = quiz['creator']
    
    if quiz_name not in question_results or not question_results[quiz_name]:
        await context.bot.send_message(chat_id=creator_id, text="No participants answered any questions.")
        return

    # Prepare the results message per question
    result_message = f"📊 *Results for Quiz '{quiz_name}':*\n\n"
    for question_index, participants in question_results[quiz_name].items():
        result_message += f"**Results for Question {question_index + 1}:**\n"
        sorted_participants = sorted(participants.items(), key=lambda x: (x[1]['correct'], -x[1]['time_taken']), reverse=True)

        for i, (user_id, result) in enumerate(sorted_participants, start=1):
            user = await context.bot.get_chat(user_id)
            result_message += f"{i}. {user.username or user.first_name}: {'Correct' if result['correct'] else 'Incorrect'} "
            if result['correct']:
                result_message += f"(answered in {result['time_taken']:.2f} seconds)\n"
            else:
                result_message += "\n"

    # Summarize the top 3 participants with the most correct answers
    correct_answers_summary = {}
    for participants in question_results[quiz_name].values():
        for user_id, result in participants.items():
            if result['correct']:
                correct_answers_summary[user_id] = correct_answers_summary.get(user_id, 0) + 1

    sorted_summary = sorted(correct_answers_summary.items(), key=lambda x: x[1], reverse=True)
    result_message += "\n🏆 **Overall Quiz Winners:**\n"
    for i, (user_id, correct_answers) in enumerate(sorted_summary[:3], start=1):
        user = await context.bot.get_chat(user_id)
        result_message += f"{i}. {user.username or user.first_name}: {correct_answers} correct answers\n"

    # Escape special characters in result_message for Markdown
    result_message = result_message.replace("_", "\\_").replace("*", "\\*")

    # Send the results privately to the creator
    try:
        await context.bot.send_message(chat_id=creator_id, text=result_message, parse_mode=ParseMode.MARKDOWN)
    except Exception as e:
        logger.error(f"Error sending results to creator: {e}")
        await context.bot.send_message(chat_id=creator_id, text="❌ An error occurred while sending the results.")

# --- /RESULTS COMMAND TO RETRIEVE RESULTS ---
async def end_quiz(update: Update, context: CallbackContext):
    args = context.args
    if not args:
        await update.message.reply_text("❌ Please provide the quiz name. Usage: /results <quiz_name>")
        return

    quiz_name = ' '.join(args)
    if quiz_name not in quizzes:
        await update.message.reply_text("❌ Quiz not found. Please provide a valid quiz name.")
        return

    # Send results to the quiz creator using the send_results_to_creator function
    await send_results_to_creator(update, context, quiz_name)

# --- DELETE QUIZ FUNCTION ---
async def delete_quiz(update: Update, context: CallbackContext):
    args = context.args
    user_id = update.message.from_user.id

    if not args:
        await update.message.reply_text("❌ You need to provide a quiz name. Usage: /deletequiz <quiz_name>")
        return

    quiz_name = ' '.join(args)
    if quiz_name not in quizzes:
        await update.message.reply_text("❌ Quiz not found. Please provide a valid quiz name.")
        return

    quiz = quizzes[quiz_name]
    if user_id != quiz['creator']:
        await update.message.reply_text("❌ Only the quiz creator can delete the quiz.")
        return

    del quizzes[quiz_name]
    await update.message.reply_text(f"🗑 The quiz '{quiz_name}' has been deleted.")

# --- MAIN FUNCTION ---
def main():
    application = Application.builder().token(bot_token).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("createquiz", create_quiz)],
        states={
            ASK_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_name)],
            ASK_QUESTION_TYPE: [CallbackQueryHandler(ask_question_type)],
            ASK_QUESTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_question)],
            ASK_OPTIONS: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_options)],
            ASK_ANSWER: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_answer)],
            ASK_TIME_GAP: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_time_gap)],
            ADD_MORE_QUESTIONS: [CallbackQueryHandler(add_more_questions)]
        },
        fallbacks=[CommandHandler("cancel", lambda update, context: update.message.reply_text("Quiz creation canceled."))]
    )

    application.add_handler(conv_handler)
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("myquizzes", my_quizzes))
    application.add_handler(CommandHandler("allcommands", all_commands))
    application.add_handler(CommandHandler("startquiz", start_quiz))
    application.add_handler(CommandHandler("deletequiz", delete_quiz))
    application.add_handler(CommandHandler("deletequiz", delete_quiz))
    application.add_handler(CommandHandler("results", end_quiz))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_answer))

    application.run_polling()

if __name__ == '__main__':
    main()