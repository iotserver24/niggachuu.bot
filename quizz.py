import asyncio
import logging
import random
from telegram import Update, Poll, InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup
from telegram.constants import ParseMode, ChatAction
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackContext, ConversationHandler, PollAnswerHandler, filters, CallbackQueryHandler

# Bot token
bot_token = '7518438812:AAF29rspjnbm48FQMZXJBCTOL1U5HOUJC-4'

# Quiz states
(ASK_NAME, ASK_QUESTION_TYPE, ASK_QUESTION, ASK_OPTIONS, ASK_ANSWER, ASK_TIME_GAP, ADD_MORE_QUESTIONS) = range(7)

# Global variables for managing quizzes and participants
quizzes = {}
quiz_participants = {}
user_quizzes = {}

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

# --- POLL ANSWER TRACKING ---
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
            correct_answer = int(update.message.text)
            context.user_data['correct_answer'] = correct_answer - 1

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

# --- START QUIZ AND SEND POLLS ---
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

    # Send the questions one by one with the specified time gap
    for idx, question_data in enumerate(quiz['questions']):
        poll_message = await context.bot.send_poll(
            chat_id=update.effective_chat.id,
            question=question_data['question'],
            options=question_data['options'],
            is_anonymous=False,  # Non-anonymous poll to track users
            type=Poll.QUIZ,
            correct_option_id=question_data['correct_answer']
        )

        # Track poll IDs for results later
        if quiz_name not in quiz_participants:
            quiz_participants[quiz_name] = {}
        quiz_participants[quiz_name]['poll_message_ids'] = poll_message.poll.id

        # Wait for the time gap between questions
        time_gap = quiz.get('time_gap', 0)
        if time_gap > 0 and idx < len(quiz['questions']) - 1:
            await update.message.reply_text(f"⏳ Next question in {time_gap} seconds...")
            await asyncio.sleep(time_gap)

# --- HANDLE POLL ANSWERS ---
async def handle_poll_answer(update: Update, context: CallbackContext):
    answer = update.poll_answer
    quiz_name = None

    # Find which quiz the poll belongs to
    for qname, data in quizzes.items():
        if 'poll_message_ids' in data and data['poll_message_ids'] == answer.poll_id:
            quiz_name = qname
            break

    if not quiz_name:
        return

    quiz = quizzes[quiz_name]
    user_id = answer.user.id

    # Track participant answers for each quiz
    if user_id not in quiz_participants[quiz_name]:
        quiz_participants[quiz_name][user_id] = {
            'correct': 0,
            'total': 0
        }

    # Check if the answer is correct and update participant's score
    correct_option_id = quiz['questions'][answer.option_ids[0]]['correct_answer']
    if answer.option_ids[0] == correct_option_id:
        quiz_participants[quiz_name][user_id]['correct'] += 1

    quiz_participants[quiz_name][user_id]['total'] += 1

# --- SEND RESULTS TO THE CREATOR PRIVATELY ---
async def end_quiz(update: Update, context: CallbackContext):
    args = context.args
    if not args:
        await update.message.reply_text("❌ Please provide the quiz name. Usage: /results <quiz_name>")
        return

    quiz_name = ' '.join(args)
    if quiz_name not in quizzes:
        await update.message.reply_text("❌ Quiz not found. Please provide a valid quiz name.")
        return

    quiz = quizzes[quiz_name]
    creator_id = quiz['creator']

    if quiz_name not in quiz_participants or len(quiz_participants[quiz_name]) <= 1:  # Check if any participant exists
        await update.message.reply_text("❌ No participants for this quiz.")
        return

    # Prepare and sort results by the number of correct answers
    sorted_participants = sorted(quiz_participants[quiz_name].items(), key=lambda x: x[1]['correct'], reverse=True)

    result_message = f"📊 Results for quiz '{quiz_name}':\n"
    for i, (user_id, scores) in enumerate(sorted_participants, start=1):
        if user_id == 'poll_message_ids':  # Skip poll_message_ids key
            continue
        user = await context.bot.get_chat(user_id)
        result_message += f"{i}. {user.username or user.first_name}: {scores['correct']} correct out of {scores['total']} questions\n"

    # Send the results only to the creator in their private chat
    try:
        await context.bot.send_message(chat_id=creator_id, text=result_message)
        await update.message.reply_text("✔ Results have been sent privately to the quiz creator.")
    except Exception as e:
        logger.error(f"Error sending results to creator: {e}")
        await update.message.reply_text("❌ An error occurred while sending the results.")

# --- RANDOM WINNER COMMAND ---
async def random_winner(update: Update, context: CallbackContext):
    chat = update.effective_chat
    user = update.effective_user

    if chat.type != "group" and chat.type != "supergroup":
        await update.message.reply_text("❌ This command can only be used in groups.")
        return

    member_status = await context.bot.get_chat_member(chat_id=chat.id, user_id=user.id)
    if member_status.status not in ['administrator', 'creator']:
        await update.message.reply_text("❌ Only admins can use this command.")
        return

    members = await context.bot.get_chat_administrators(chat.id)
    members_list = [member.user for member in members if not member.user.is_bot]

    if members_list:
        winner = random.choice(members_list)
        await update.message.reply_text(f"🎉 The winner is @{winner.username or winner.first_name}! 🏆🎊")
    else:
        await update.message.reply_text("❌ No eligible users found in this group.")

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
    application.add_handler(CommandHandler("results", end_quiz))
    application.add_handler(CommandHandler("random", random_winner))
    application.add_handler(PollAnswerHandler(handle_poll_answer))

    application.run_polling()


if __name__ == '__main__':
    main()