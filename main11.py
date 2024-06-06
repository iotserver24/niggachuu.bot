import telebot
from telebot import types
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import time
import re
from datetime import timedelta, datetime
import sqlite3

API_TOKEN = '7118337070:AAGWms98JO3Qqu_fyEmNeeOIINKrQy4dpAA'

bot = telebot.TeleBot(API_TOKEN, parse_mode='HTML')

user_join_status = {}
user_states = {}
started_users = set()
banned_users = set()
broad_users = []

def has_joined_required_groups(user_id):
    try:
        auction_status = bot.get_chat_member(chat_id="@VA_HEXA_TRADE", user_id=user_id).status
        trade_status = bot.get_chat_member(chat_id="@VA_HEXA_TRADE", user_id=user_id).status
        has_joined_auction = auction_status in ['member', 'administrator', 'creator']
        has_joined_trade = trade_status in ['member', 'administrator', 'creator']
    except:
        has_joined_auction = False
        has_joined_trade = False
    return has_joined_auction and has_joined_trade

def send_welcome_message(chat_id, username, first_name):
    markup = types.InlineKeyboardMarkup()
    join_auction_btn = types.InlineKeyboardButton("Join Auction", url="https://t.me/VA_HEXA_AUCTION")
    join_trade_btn = types.InlineKeyboardButton("Join Trade", url="https://t.me/VA_HEXA_TRADE")
    joined_btn = types.InlineKeyboardButton("Joined", callback_data="joined")

    markup.add(join_auction_btn, join_trade_btn)
    markup.add(joined_btn)

    caption = (
        f"<b>🔸Welcome, {first_name} To VA Auction Bot</b>\n\n"
        "<b>🔸You Can Submit Your Pokemon Through This Bot For Auction</b>\n\n"
        "<b>🔻But Before Using You Have To Join Our Auction Group By Clicking Below Two Buttons And Then Click 'Joined' Button</b>"
    )

    bot.send_photo(
        chat_id,
        photo="https://wallpapers.com/images/hd/legendary-pokemon-pictures-7yo7x0f1l2b2tu0r.jpg",
        caption=caption,
        reply_markup=markup,
        parse_mode='HTML',
    )

@bot.message_handler(commands=['start'])
def handle_start(message):
    if str(message.from_user.id) in banned_users:
        bot.reply_to(message, "<b>You Are Banned By an Administrator</b>")
    else:
        if message.chat.type == 'private':
            user_id = message.chat.id
            if user_id not in broad_users:
                broad_users.append(user_id)
            if not has_joined_required_groups(user_id):
                send_welcome_message(message.chat.id, message.from_user.username, message.from_user.first_name)
                started_users.add(user_id)
            else:
                bot.reply_to(message, "<b>You have already joined the required groups. Feel free to use the bot.</b>")
                started_users.add(user_id)
        else:
            markup = types.InlineKeyboardMarkup()
            button = types.InlineKeyboardButton("Go to Bot PM", url=f"t.me/{bot.get_me().username}")
            markup.add(button)
            bot.reply_to(message, "<b>This command can only be used in private messages.</b>", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "joined")
def handle_joined(call):
    user_id = call.from_user.id
    if has_joined_required_groups(user_id):
        bot.edit_message_caption(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            caption="<b>Thanks for joining our groups 😊</b>"
        )
    else:
        bot.answer_callback_query(callback_query_id=call.id, text="You must join all required groups to proceed.", show_alert=True)

@bot.message_handler(commands=['cancel'])
def handle_cancel(message):
    if str(message.from_user.id) in banned_users:
        bot.reply_to(message, "<b>You Are Banned By an Administrator</b>", parse_mode='HTML')
    else:
        if message.chat.type == 'private':
            user_id = message.from_user.id
            if user_id in user_states:
                del user_states[user_id] 
            bot.send_message(message.chat.id, "<b>All Running Command Has Been Cancelled ✅</b>", parse_mode='HTML')
        else:
            markup = types.InlineKeyboardMarkup()
            button = types.InlineKeyboardButton("Go to Bot PM", url=f"t.me/{bot.get_me().username}")
            markup.add(button)
            bot.reply_to(message, "<b>This command can only be used in private messages.</b>", parse_mode='HTML', reply_markup=markup)

def is_admin(user_id):
    admin_ids = [5257885057, 5690812882, 6694887060, 7387719195, 6541873974]
    return user_id in admin_ids

@bot.message_handler(commands=['natures'])
def handle_natures(message):
    if str(message.from_user.id) in banned_users:
        bot.reply_to(message, "<b>You Are Banned By an Administrator</b>")
    else:
        photo_url = "https://t.me/AcnHexaAuctionTrade/4880771"  
        caption = "<b>Here Is The List Of All Natures</b>"
        bot.send_photo(message.chat.id, photo=photo_url, caption=caption)

nature_info = {
    "adamant": {"increase": "Attack", "decrease": "Special Attack"},
    "bashful": {"increase": "none", "decrease": "none"},
    "bold": {"increase": "Defense", "decrease": "Attack"},
    "brave": {"increase": "Attack", "decrease": "Speed"},
    "calm": {"increase": "Special Defense", "decrease": "Attack"},
    "careful": {"increase": "Special Defense", "decrease": "Special Attack"},
    "docile": {"increase": "none", "decrease": "none"},
    "gentle": {"increase": "Special Defense", "decrease": "Defense"},
    "hardy": {"increase": "none", "decrease": "none"},
    "hasty": {"increase": "Speed", "decrease": "Defense"},
    "impish": {"increase": "Defense", "decrease": "Special Attack"},
    "jolly": {"increase": "Speed", "decrease": "Special Attack"},
    "lax": {"increase": "Defense", "decrease": "Special Defense"},
    "lonely": {"increase": "Attack", "decrease": "Defense"},
    "mild": {"increase": "Special Attack", "decrease": "Defense"},
    "modest": {"increase": "Special Attack", "decrease": "Attack"},
    "naive": {"increase": "Speed", "decrease": "Special Defense"},
    "naughty": {"increase": "Attack", "decrease": "Special Defense"},
    "quiet": {"increase": "Special Attack", "decrease": "Speed"},
    "quirky": {"increase": "none", "decrease": "none"},
    "rash": {"increase": "Special Attack", "decrease": "Special Defense"},
    "relaxed": {"increase": "Defense", "decrease": "Speed"},
    "sassy": {"increase": "Special Defense", "decrease": "Speed"},
    "serious": {"increase": "none", "decrease": "none"},
    "timid": {"increase": "Speed", "decrease": "Attack"}
}

@bot.message_handler(func=lambda message: message.text.lower() in nature_info)
def handle_nature(message):
    nature_name = message.text.lower()
    info = nature_info[nature_name]
    response = f"<b>Nature : {nature_name.capitalize()}\n\n▪️ Effects :-\n</b>"
    response += f"<b>🔺 Stats Increase + : {info['increase']}\n</b>"
    response += f"<b>🔻 Stats Decrease - : {info['decrease']}\n</b>"
    bot.reply_to(message, response)

@bot.message_handler(commands=['sellerinfo'])
def handle_seller_info(message):
    if str(message.from_user.id) in banned_users:
        bot.reply_to(message, "<b>You Are Banned By an Administrator</b>")
    else:
        if message.chat.type == 'private':
            info_message = (
                "<b>To Find a Seller :</b>\n\n"
                "<b>🔹 /seller (name) (nature) (level)</b>"
            )
            bot.send_message(message.chat.id, info_message, parse_mode='HTML')
        else:
                markup = types.InlineKeyboardMarkup()
                button = types.InlineKeyboardButton("Go to Bot PM", url=f"t.me/{bot.get_me().username}")
                markup.add(button)
                bot.reply_to(message, "<b>This command can only be used in private messages.</b>", reply_markup=markup)

@bot.message_handler(commands=['admin'])
def handle_admin(message):
    if str(message.from_user.id) in banned_users:
        bot.reply_to(message, "<b>You Are Banned By an Administrator</b>")
    else:
        if message.chat.type == 'private':
            admin_list = ["@" + "SoulReaperCommercial"] 
            admin_message = "<b>All Admin of Bot Are :</b>\n\n"
            for i, admin_username in enumerate(admin_list, start=1):
                admin_message += f"{i}. <b>{admin_username}</b>\n"
            bot.send_message(message.chat.id, admin_message, parse_mode='HTML')
        else:
                markup = types.InlineKeyboardMarkup()
                button = types.InlineKeyboardButton("Go to Bot PM", url=f"t.me/{bot.get_me().username}")
                markup.add(button)
                bot.reply_to(message, "<b>This command can only be used in private messages.</b>", reply_markup=markup)

@bot.message_handler(commands=['help'])
def handle_cmds(message):
    if message.chat.type == 'private':
        if str(message.from_user.id) in banned_users:
            bot.reply_to(message, "<b>You Are Banned By an Administrator</b>", parse_mode='HTML')
        else:
            user_id = message.from_user.id
            bot.reply_to(message, '''
<b>Users Commands :</b>
—————————————————————————
• <b>/start</b> - Start the Bot
• <b>/add</b> - Add Pokes / Items in Auction 
• <b>/cancel</b> - Cancel All commands
• <b>/item</b> - Get items In Auction
• <b>/natures</b> - Get Nature Info
• <b>/seller</b> - Get Seller username for a Item
• <b>/sellerinfo</b> - Get Seller Info
• <b>/sellers</b> - All sellers In auction 
• <b>/profile</b> - Get your profile or Reply to Someone to Get His Profile
• <b>/admin</b> - Get All admins in Bot
• <b>/help</b> - Get This Message
• <b>/users</b> - Get Total Users in bot 
• <b>/host</b> - Create Auction Bot
                     
<b>Admin commands :</b>
—————————————————————————
• <b>/list</b> - Get List of Pokemon / TMs In Auction (Admin)
• <b>/sold</b> - Sold Messenger (Admin)
• <b>/unsold</b> - Unsold Messenger (Admin)
• <b>/ban</b> - Ban Someone (Admin)
• <b>/unban</b> - Unban Someone (Admin)
• <b>/msg</b> - Message a User (Admin)
• <b>/current</b> - Get current Slot For Auction (Admin)
• <b>/broad</b> - Broadcast A Message (Admin)
• <b>/forward</b> - Forward a Message (Admin)
• <b>/buyers</b> - Get all buyers in auction (Admin)
• <b>/next</b> - Send next item in Auction (Admin)
                     
<b>Owner commands :</b>
—————————————————————————                     
• <b>/clear</b> - Clear all Slots (Owner)
• <b>/approve</b> - Approve Someone (Owner)
''', parse_mode='HTML')
    else:
                markup = types.InlineKeyboardMarkup()
                button = types.InlineKeyboardButton("Go to Bot PM", url=f"t.me/{bot.get_me().username}")
                markup.add(button)
                bot.reply_to(message, "<b>This command can only be used in private messages.</b>", reply_markup=markup)

@bot.message_handler(commands=['users'])
def handle_users(message):
    if message.chat.type == 'private':
        if str(message.from_user.id) in banned_users:
            bot.reply_to(message, "<b>You Are Banned By an Administrator</b>", parse_mode='HTML')
        else:
            num_users = len(started_users)
            bot.reply_to(message, f"<b>All users in Bot are : {num_users}</b>", parse_mode='HTML')
    else:
        markup = types.InlineKeyboardMarkup()
        button = types.InlineKeyboardButton("Go to Bot PM", url=f"t.me/{bot.get_me().username}")
        markup.add(button)
        bot.reply_to(message, "<b>This command can only be used in private messages.</b>", parse_mode='HTML', reply_markup=markup)

@bot.message_handler(commands=['host'])
def send_host(message):
    if str(message.from_user.id) in banned_users:
        bot.reply_to(message, "<b>You Are Banned By an Administrator</b>")
    else:
        if message.chat.type == 'private':
            host_message = "<b>Want To Create Auction Bot Like This?</b>"
            markup = InlineKeyboardMarkup()
            btn = InlineKeyboardButton(text='Contact', url='https://t.me/SoulReaperCommercial')
            markup.add(btn)
        
            bot.reply_to(message, host_message, reply_markup=markup)
        else:
            markup = types.InlineKeyboardMarkup()
            button = types.InlineKeyboardButton("Go to Bot PM", url=f"t.me/{bot.get_me().username}")
            markup.add(button)
            bot.reply_to(message, "</b>This command can only be used in private messages.</b>", reply_markup=markup)

sold_items = []

message_store = {}
previous_dot_message = {}
current_index = 0
confirmed_messages = set()

admin_ids = [5257885057, 5690812882, 6694887060, 7387719195, 6541873974]

@bot.message_handler(func=lambda message: message.text == "." and message.from_user.id in admin_ids)
def handle_dot(message):
    chat_id = message.chat.id

    if chat_id in previous_dot_message:
        prev_msg_id = previous_dot_message[chat_id]
        if prev_msg_id not in confirmed_messages:
            try:
                bot.delete_message(chat_id, prev_msg_id)
            except Exception as e:
                print(f"Failed to delete message: {e}")

    msg = bot.reply_to(message, "<b>•</b>", parse_mode='HTML')
    previous_dot_message[chat_id] = msg.message_id

    time.sleep(1.5)
    bot.edit_message_text("<b>• •</b>", chat_id, msg.message_id, parse_mode='HTML')
    time.sleep(1.5)
    bot.edit_message_text("<b>• • •</b>", chat_id, msg.message_id, parse_mode='HTML')
    time.sleep(1.5)

    reply_username = message.reply_to_message.from_user.username if message.reply_to_message else "Unknown"
    reply_text = message.reply_to_message.text if message.reply_to_message else "Unknown"

    if not re.match(r'^\d+(k|pd)?$', reply_text):
        bot.reply_to(message, "<b>Invalid format. Please enter a valid integer value (e.g., 1, 2, 1k, 2pd).</b>", parse_mode='HTML')
        return

    confirmation_text = f"<b>Sure Sell To @{reply_username} For {reply_text}?</b>"

    keyboard = types.InlineKeyboardMarkup()
    yes_button = types.InlineKeyboardButton(text="yes", callback_data=f"sell_pokemon_{chat_id}_{msg.message_id}")
    keyboard.add(yes_button)
    bot.edit_message_text(confirmation_text, chat_id, msg.message_id, reply_markup=keyboard, parse_mode='HTML')

    message_store[f"{chat_id}_{msg.message_id}"] = message

@bot.callback_query_handler(func=lambda call: call.data.startswith("sell_pokemon_"))
def handle_sell_pokemon(call):
    if call.from_user.id not in admin_ids:
        bot.answer_callback_query(call.id, text="🖕", parse_mode='HTML')
        return

    data = call.data.split("_")
    chat_id = int(data[2])
    message_id = int(data[3])

    confirmed_messages.add(message_id)

    original_message = message_store.get(f"{chat_id}_{message_id}")
    if not original_message:
        bot.answer_callback_query(call.id, text="<b>Original message not found.</b>", parse_mode='HTML')
        return

    reply_username = original_message.reply_to_message.from_user.username if original_message.reply_to_message else "Unknown"
    reply_text = original_message.reply_to_message.text if original_message.reply_to_message else "Unknown"

    sold_items.append((reply_username, reply_text))

@bot.message_handler(commands=['sold'])
def handle_sold(message):
    if message.from_user.id not in admin_ids:
        bot.reply_to(message, "<b>You are not authorized to use this command.</b>", parse_mode='HTML')
        return

    try:
        command, item_name = message.text.split(' ', 1)
        username = message.reply_to_message.from_user.username if message.reply_to_message else None
        amount = message.reply_to_message.text if message.reply_to_message else None

        if not username or not amount:
            bot.reply_to(message, "<b>Please reply to a message with the username and amount.</b>", parse_mode='HTML')
            return

        sold_items.append((item_name, username, amount))

        reply_message = (f"<b>🔊 {item_name} Has Been Sold</b>\n\n"
                         f"<b>🔸 Sold to - @{username}</b>\n"
                         f"<b>🔸 Sold for - {amount}</b>\n\n"
                         "❗ <b>Join <a href='@VA_HEXA_TRADE'>Trade Group</a> To Get Seller Username After Auction</b>")

        sent_message = bot.reply_to(message, reply_message, parse_mode='HTML', disable_web_page_preview=True)
        bot.pin_chat_message(message.chat.id, sent_message.message_id)

    except ValueError:
        bot.reply_to(message, "<b>Please provide the command in the format /sold item_name</b>", parse_mode='HTML')

@bot.message_handler(commands=['buyers'])
def handle_buyers(message):
    if not sold_items:
        bot.reply_to(message, "No buyers yet.", parse_mode='HTML')
        return

    buyers_list = "<b>Here are the Buyers:</b>\n\n"
    for i, (item_name, username, amount) in enumerate(sold_items, start=1):
        buyers_list += f"🔹 {item_name} - Sold to @{username} - Sold for {amount}\n"

    bot.reply_to(message, buyers_list, parse_mode='HTML')


@bot.message_handler(commands=['unsold'])
def handle_unsold(message):
    if is_admin(message.from_user.id):
        try:
            pokemon_name = message.text.split(' ', 1)[1]
            reply_message = f"<b>❌ {pokemon_name} Has Been Unsold</b>"
            sent_message = bot.reply_to(message, reply_message, parse_mode='HTML')
            bot.pin_chat_message(message.chat.id, sent_message.id)  
        except IndexError:
            bot.reply_to(message, "<b>Please provide the name of the Pokemon to mark as unsold.</b>")
    else:
        bot.reply_to(message, "<b>You are not authorized to use this command.</b>")

@bot.message_handler(commands=['ban'])
def handle_ban(message):
    if str(message.from_user.id) in banned_users:
        bot.reply_to(message, "<b>You Are Banned By an Administrator</b>", parse_mode='HTML')
    else:
        if str(message.from_user.id) not in str(admin_ids):
            bot.reply_to(message, "<b>You are not authorized to use this command.</b>", parse_mode='HTML')
            return

        try:
            _, user_id = message.text.split(maxsplit=1)
            banned_users.add(user_id)  
            bot.reply_to(message, f"<b>User with ID {user_id} has been banned.</b>", parse_mode='HTML')
        except ValueError:
            bot.reply_to(message, "<b>Invalid syntax. Use /ban <user_id></b>", parse_mode='HTML')


@bot.message_handler(commands=['unban'])
def handle_unban(message):
    if str(message.from_user.id) in banned_users:
        bot.reply_to(message, "<b>You Are Banned By an Administrator</b>", parse_mode='HTML')
    else:
        if str(message.from_user.id) not in str(admin_ids):
            bot.reply_to(message, "<b>You are not authorized to use this command.</b>", parse_mode='HTML')
            return
        try:
            _, user_id = message.text.split(maxsplit=1)
            if user_id in banned_users:
                banned_users.remove(user_id) 
                bot.reply_to(message, f"<b>User with ID {user_id} has been unbanned.</b>", parse_mode='HTML')
            else:
                bot.reply_to(message, f"<b>User with ID {user_id} is not banned.</b>", parse_mode='HTML')
        except ValueError:
            bot.reply_to(message, "<b>Invalid syntax. Use /unban <user_id></b>", parse_mode='HTML')

@bot.message_handler(commands=['msg'])
def handle_msg(message):
    if str(message.from_user.id) in banned_users:
        bot.reply_to(message, "<b>You Are Banned By an Administrator</b>", parse_mode='HTML')
    else:
        if message.from_user.id not in admin_ids:
            bot.reply_to(message, "<b>You are not authorized to use this command.</b>", parse_mode='HTML')
            return

        try:
            _, user_id, user_message = message.text.split(maxsplit=2)
            user_id = int(user_id)
        except ValueError:
            bot.reply_to(message, "<b>Invalid syntax. Use /msg (user_id) (message)</b>", parse_mode='HTML')
            return

        try:
            bot.send_message(user_id, user_message)
            bot.reply_to(message, f"<b>Message sent to user {user_id}</b>", parse_mode='HTML')
        except Exception as e:
            bot.reply_to(message, f"<b>Failed to send message to user {user_id}: {e}</b>", parse_mode='HTML')

admin_ids_broad = ["5257885057", "5690812882", "6694887060", "7387719195", "6541873974"]

@bot.message_handler(commands=['broad'])
def broadcast(message):
    if str(message.from_user.id) in banned_users:
        bot.reply_to(message, "<b>You Are Banned By an Administrator</b>", parse_mode='HTML')
    else:
        user_id = message.chat.id
        if str(user_id) in admin_ids_broad:
            if len(message.text.split()) >= 2:
                broadcast_message = ' '.join(message.text.split()[1:])
                for user_id in broad_users:
                    bot.send_message(user_id, broadcast_message)
                bot.reply_to(message, f"<b>Broadcast sent to all {len(broad_users)} users.</b>", parse_mode='HTML')
            else:
                bot.reply_to(message, "<b>Please provide a message to broadcast using the syntax /broad (message).</b>", parse_mode='HTML')
        else:
            bot.reply_to(message, "<b>You're not authorized to perform this action.</b>", parse_mode='HTML')

group_id = -1002194151018

@bot.message_handler(commands=['forward'])
def send_message_prompt(message):
    if str(message.from_user.id) in banned_users:
        bot.reply_to(message, "<b>You Are Banned By an Administrator</b>", parse_mode='HTML')
    else:
        if is_admin(message.from_user.id):
            bot.reply_to(message, "<b>Type the message to send in the group</b>", parse_mode='HTML')
            bot.register_next_step_handler(message, send_message)
        else:
            bot.reply_to(message, "<b>Only admins can perform this action.</b>", parse_mode='HTML')

def send_message(message):
    if str(message.from_user.id) in banned_users:
        bot.reply_to(message, "You Are Banned By an Administrator")
    else:
        if message.forward_from or message.forward_from_chat:
            forwarded_message = message
        else:
            forwarded_message = message.text
        try:
            bot.forward_message(group_id, message.chat.id, message.id)
            bot.send_message(message.chat.id, "<b>Message sent successfully.</b>")
        except Exception as e:
            bot.send_message(message.chat.id, f"</b>Failed to send message: {e}</b>")

owner_id = 7387719195

@bot.message_handler(commands=['approve'])
def handle_approve(message):
    if str(message.from_user.id) in banned_users:
        bot.reply_to(message, "<b>You Are Banned By an Administrator</b>", parse_mode='HTML')
        return
    
    if message.reply_to_message:
        if str(message.from_user.id) == str(owner_id):
            user_id = message.reply_to_message.from_user.id
            if user_id not in admin_ids:
                admin_ids.append(user_id)
                admin_ids_broad.append(str(user_id))
                bot.reply_to(message, f"<b>User with ID {user_id} has been approved as admin.</b>", parse_mode='HTML')
            else:
                bot.reply_to(message, f"<b>User with ID {user_id} is already an admin.</b>", parse_mode='HTML')
        else:
            bot.reply_to(message, "<b>Only the bot owner can perform this action.</b>", parse_mode='HTML')
    else:
        bot.reply_to(message, "<b>Please reply to a user's message to approve them as an admin.</b>", parse_mode='HTML')

group_id_mute = -1002194151018 
mute_duration = 2 * 60 

def mute_user(chat_id, user_id, duration_seconds):
    until_date = datetime.now() + timedelta(seconds=duration_seconds)
    bot.restrict_chat_member(chat_id, user_id, can_send_messages=False, until_date=until_date)

admin_id_mute = [] 

def is_member_of_group(user_id, group_id):
    try:
        group_id = 'https://t.me/VA_HEXA_TRADE'
        chat_member = bot.get_chat_member(group_id, user_id)
        if chat_member.status in ['member', 'administrator', 'creator']:
            return True
        else:
            return False
    except telebot.apihelper.ApiException:
        return False

@bot.message_handler(content_types=['new_chat_members'])
def handle_new_members(message):
    new_members = message.new_chat_members
    for member in new_members:
        user_id = member.id
        if user_id in admin_id_mute:
            continue

        if not is_member_of_group(user_id, group_id_mute):
            mute_user(message.chat.id, user_id, mute_duration)
            bot.reply_to(message, f"<b>Muted {member.first_name} for 2 minutes.</b>\n"
                                              f"<b>Reason: Not Found In <a href='https://t.me/VA_HEXA_TRADE'> Trade Group</a> </b>", disable_web_page_preview=True)

tm_data = {
    2: {"name": "Dragon Claw", "power": 80, "accuracy": 100, "category": "P"},
    3: {"name": "Psyshock", "power": 80, "accuracy": 100, "category": "S"},
    9: {"name": "Venoshock", "power": 65, "accuracy": 100, "category": "S"},
    10: {"name": "Hidden Power", "power": 60, "accuracy": 100, "category": "S"},
    13: {"name": "Ice Beam", "power": 90, "accuracy": 100, "category": "S"},
    14: {"name": "Blizzard", "power": 110, "accuracy": 70, "category": "S"},
    15: {"name": "Hyper Beam", "power": 150, "accuracy": 90, "category": "S"},
    22: {"name": "Solar Beam", "power": 120, "accuracy": 100, "category": "S"},
    23: {"name": "Smack Down", "power": 50, "accuracy": 100, "category": "P"},
    24: {"name": "Thunderbolt", "power": 90, "accuracy": 100, "category": "S"},
    25: {"name": "Thunder", "power": 110, "accuracy": 70, "category": "P"},
    26: {"name": "Earthquake", "power": 100, "accuracy": 100, "category": "P"},
    28: {"name": "Leech Life", "power": 80, "accuracy": 100, "category": "P"},
    29: {"name": "Psychic", "power": 90, "accuracy": 100, "category": "S"},
    30: {"name": "Shadow Ball", "power": 80, "accuracy": 100, "category": "S"},
    31: {"name": "Brick Break", "power": 75, "accuracy": 100, "category": "P"},
    34: {"name": "Sludge Wave", "power": 95, "accuracy": 100, "category": "S"},
    35: {"name": "Flamethrower", "power": 90, "accuracy": 100, "category": "S"},
    36: {"name": "Sludge Bomb", "power": 90, "accuracy": 100, "category": "S"},
    38: {"name": "Fire Blast", "power": 110, "accuracy": 85, "category": "S"},
    39: {"name": "Rock Tomb", "power": 60, "accuracy": 95, "category": "P"},
    40: {"name": "Aerial Ace", "power": 60, "accuracy": 100, "category": "P"},
    42: {"name": "Facade", "power": 70, "accuracy": 100, "category": "P"},
    43: {"name": "Flame Charge", "power": 50, "accuracy": 100, "category": "P"},
    46: {"name": "Thief", "power": 60, "accuracy": 100, "category": "P"},
    47: {"name": "Low Sweep", "power": 65, "accuracy": 100, "category": "P"},
    48: {"name": "Round", "power": 60, "accuracy": 100, "category": "S"},
    49: {"name": "Echoed Voice", "power": 40, "accuracy": 100, "category": "S"},
    50: {"name": "Overheat", "power": 130, "accuracy": 90, "category": "S"},
    51: {"name": "Steel Wing", "power": 70, "accuracy": 90, "category": "P"},
    52: {"name": "Focus Blast", "power": 120, "accuracy": 70, "category": "S"},
    53: {"name": "Energy Ball", "power": 90, "accuracy": 100, "category": "S"},
    54: {"name": "False Swipe", "power": 40, "accuracy": 100, "category": "P"},
    55: {"name": "Scald", "power": 80, "accuracy": 100, "category": "S"},
    57: {"name": "Charge Beam", "power": 50, "accuracy": 90, "category": "S"},
    58: {"name": "Sky Drop", "power": 60, "accuracy": 100, "category": "P"},
    59: {"name": "Brutal Swing", "power": 60, "accuracy": 100, "category": "P"},
    62: {"name": "Acrobatics", "power": 55, "accuracy": 100, "category": "P"},
    65: {"name": "Shadow Claw", "power": 70, "accuracy": 100, "category": "P"},
    66: {"name": "Payback", "power": 50, "accuracy": 100, "category": "P"},
    67: {"name": "Smart Strike", "power": 70, "accuracy": 100, "category": "P"},
    68: {"name": "Giga Impact", "power": 150, "accuracy": 90, "category": "P"},
    71: {"name": "Stone Edge", "power": 100, "accuracy": 80, "category": "P"},
    72: {"name": "Volt Switch", "power": 70, "accuracy": 100, "category": "S"},
    76: {"name": "Fly", "power": 90, "accuracy": 95, "category": "P"},
    78: {"name": "Bulldoze", "power": 60, "accuracy": 100, "category": "P"},
    79: {"name": "Frost Breath", "power": 60, "accuracy": 90, "category": "S"},
    80: {"name": "Rock Slide", "power": 75, "accuracy": 90, "category": "P"},
    81: {"name": "X-Scissor", "power": 80, "accuracy": 100, "category": "P"},
    82: {"name": "Dragon Tail", "power": 60, "accuracy": 90, "category": "P"},
    83: {"name": "Infestation", "power": 70, "accuracy": 100, "category": "S"},
    84: {"name": "Poison Jab", "power": 80, "accuracy": 100, "category": "P"},
    85: {"name": "Dream Eater", "power": 100, "accuracy": 100, "category": "S"},
    89: {"name": "U-Turn", "power": 70, "accuracy": 100, "category": "P"},
    91: {"name": "Flash Cannon", "power": 80, "accuracy": 100, "category": "S"},
    93: {"name": "Wild Charge", "power": 90, "accuracy": 100, "category": "P"},
    94: {"name": "Surf", "power": 90, "accuracy": 100, "category": "S"},
    95: {"name": "Snarl", "power": 55, "accuracy": 95, "category": "S"},
    97: {"name": "Dark Pulse", "power": 80, "accuracy": 100, "category": "S"},
    98: {"name": "Waterfall", "power": 80, "accuracy": 100, "category": "P"},
    99: {"name": "Dazzling Gleam", "power": 80, "accuracy": 100, "category": "S"},
}

@bot.message_handler(func=lambda message: re.match(r'/tm\d{2}', message.text.lower()))
def handle_tm_input(message):
    match = re.match(r'/tm(\d{2})', message.text.lower())
    tm_number = int(match.group(1))
    
    if tm_number not in tm_data:
        bot.reply_to(message, "<b>TM not found. Please check the TM number and try again.</b>", parse_mode='HTML')
        return
    
    tm_info = tm_data[tm_number]
    category = "Physical" if tm_info["category"] == "P" else "Special"
    response_message = (
        f"<b>TM{tm_number} 💿 :\n\n</b>"
        f"<b>{tm_info['name']} [{category}]\n</b>"
        f"<b>Power: {tm_info['power']}, Accuracy: {tm_info['accuracy']}\n\n</b>"
        f"<b>You can sell this TM for PDs 💵 in hexa</b>"
    )
    
    bot.reply_to(message, response_message, parse_mode='HTML')

@bot.message_handler(commands=['tms'])
def show_tms(message):
    tms_list = "<b>List of TMs:</b>\n\n"
    for tm_number, tm_info in tm_data.items():
        category = "Physical" if tm_info["category"] == "P" else "Special"
        tm_info_str = f"<b>TM{tm_number} - {tm_info['name']} [{category}]</b>\n"
        tms_list += tm_info_str
    
    bot.reply_to(message, tms_list, parse_mode='HTML')

@bot.message_handler(commands=['profile'])
def send_profile(message):
    if str(message.from_user.id) in banned_users:
        bot.reply_to(message, "<b>You Are Banned By an Administrator</b>", parse_mode='HTML')
    else:
        user_id = message.from_user.id
        user_name = message.from_user.first_name
        is_verified = user_id in admin_ids or user_id in admin_ids_broad 
        profile_message = f"<b>👤 Here's Profile Of {user_name}🫧\n\n</b>"
        profile_message += f"<b>• 👉 Name: {user_name}\n</b>"
        profile_message += f"<b>• 🆔 ID: {user_id}\n\n</b>"
        profile_message += "<b>★➖➖➖➖➖➖➖➖➖➖☆\n</b>"
        profile_message += f"<b>┃╸ ©️ Verified? - {'✅' if is_verified else '❌'}\n</b>"
        profile_message += "<b>★➖➖➖➖➖➖➖➖➖➖☆</b>"
    
        bot.reply_to(message, profile_message, parse_mode='HTML')

ADMIN_CHAT_ID = '7387719195'
GROUP_CHAT_ID = '-1002194151018'

conn = sqlite3.connect('auction_items.db')
cursor = conn.cursor()

cursor.execute('''
    CREATE TABLE IF NOT EXISTS items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        type TEXT NOT NULL,
        name TEXT NOT NULL
    )
''')
conn.commit()

auction_messages = []

@bot.message_handler(commands=['add'], func=lambda message: message.chat.type == 'private' and str(message.from_user.id) not in banned_users)
def send_add_options(message):
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(types.InlineKeyboardButton("Pokemon", callback_data="add_pokemon"),
               types.InlineKeyboardButton("TMs", callback_data="add_tms"),
               types.InlineKeyboardButton("Teams", callback_data="add_teams"))
    bot.reply_to(message, "<b>What do you want to add?</b>", parse_mode="HTML", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("add_") and str(call.from_user.id) not in banned_users)
def handle_add_options(call):
    option = call.data.split("_")[1]
    if option == "pokemon":
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text="<b>Tell the name of the Pokemon:</b>", parse_mode="HTML")
        bot.register_next_step_handler(call.message, get_pokemon_name)
    elif option == "tms":
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text="<b>Provide the name of the TMs:</b>", parse_mode="HTML")
        bot.register_next_step_handler(call.message, get_tms_name)
    elif option == "teams":
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text="<b>Tell the name of the Team:</b>", parse_mode="HTML")
        bot.register_next_step_handler(call.message, get_team_name)

def get_pokemon_name(message):
    name = message.text
    bot.send_message(message.chat.id, "<b>Send a picture of the Pokemon:</b>", parse_mode="HTML")
    bot.register_next_step_handler(message, get_pokemon_picture, name)

def get_pokemon_picture(message, name):
    if not message.photo:
        bot.send_message(message.chat.id, "<b>Please send only a photo.</b>", parse_mode="HTML")
        bot.register_next_step_handler(message, get_pokemon_picture, name)
        return

    picture = message.photo[-1].file_id
    bot.send_message(message.chat.id, "<b>Provide the Pokemon's info (include Lv, Nature, Types):</b>", parse_mode="HTML")
    bot.register_next_step_handler(message, get_pokemon_info, name, picture)

def get_pokemon_info(message, name, picture):
    info = message.text
    level = None
    nature = None
    try:
        level = int(info.split('Lv. ')[1].split(' ')[0]) 
        nature = info.split('Nature: ')[1].split('\n')[0] 
    except (IndexError, ValueError):
        bot.send_message(message.chat.id, "<b>Please provide the info in the format 'Lv. 100 | Nature: Lax'</b>", parse_mode="HTML")
        bot.register_next_step_handler(message, get_pokemon_info, name, picture)
        return

    bot.send_message(message.chat.id, "<b>Provide the Pokemon's IV/EV stats:</b>", parse_mode="HTML")
    bot.register_next_step_handler(message, get_pokemon_ivev, name, picture, info, level, nature)

def get_pokemon_ivev(message, name, picture, info, level, nature):
    ivev = message.text
    bot.send_message(message.chat.id, "<b>Provide the Pokemon's moveset:</b>", parse_mode="HTML")
    bot.register_next_step_handler(message, get_pokemon_moveset, name, picture, info, level, nature, ivev)

def get_pokemon_moveset(message, name, picture, info, level, nature, ivev):
    moveset = message.text
    bot.send_message(message.chat.id, "<b>Is It Boosted ?:</b>", parse_mode="HTML")
    bot.register_next_step_handler(message, get_pokemon_boosted, name, picture, info, level, nature, ivev, moveset)

def get_pokemon_boosted(message, name, picture, info, level, nature, ivev, moveset):
    boosted = message.text
    bot.send_message(message.chat.id, "<b>Provide the Pokemon's base :</b>", parse_mode="HTML")
    bot.register_next_step_handler(message, get_pokemon_base, name, picture, info, level, nature, ivev, moveset, boosted)

def get_pokemon_base(message, name, picture, info, level, nature, ivev, moveset, boosted):
    base = message.text
    user_id = message.from_user.id
    user_name = message.from_user.username

    caption = (f"<b>Name: {name} </b> \n\n<b>Info: \n\n {info}</b>\n\n<b>IV/EV:\n\n {ivev} </b> \n\n<b>Moveset: \n\n{moveset}</b> \n\n"
               f"<b>Boosted: {boosted}</b>\n\n<b>Base: {base} </b> \n\n<b>UserID :  {user_id}</b>")
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("Approve", callback_data=f"approve_pokemon_{user_id}_{name}_{user_name}"),
               types.InlineKeyboardButton("Reject", callback_data=f"reject_pokemon_{user_id}_{name}"))
    
    auction_message = bot.send_photo(ADMIN_CHAT_ID, picture, caption=caption, parse_mode="HTML", reply_markup=markup)
    auction_messages.append(auction_message)

def get_tms_name(message):
    name = message.text
    bot.send_message(message.chat.id, "<b>Provide the info for the TMs:</b>", parse_mode="HTML")
    bot.register_next_step_handler(message, get_tms_info, name)

def get_tms_info(message, name):
    info = message.text
    bot.send_message(message.chat.id, "<b>Provide the base stats for the TMs:</b>", parse_mode="HTML")
    bot.register_next_step_handler(message, get_tms_base, name, info)

def get_tms_base(message, name, info):
    base = message.text
    user_id = message.from_user.id
    user_name = message.from_user.username

    caption = f"<b>TMs Name:</b> {name}\n<b>TMs Info:</b> {info}\n<b>Base:</b> {base}\n<b>UserID:</b> {user_id}"
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("Approve", callback_data=f"approve_tms_{user_id}_{user_name}"),
               types.InlineKeyboardButton("Reject", callback_data=f"reject_tms_{user_id}"))
    
    auction_message = bot.send_message(ADMIN_CHAT_ID, caption, parse_mode="HTML", reply_markup=markup)
    auction_messages.append(auction_message)

@bot.callback_query_handler(func=lambda call: call.data.startswith(("approve_tms_", "reject_tms_")))
def handle_tms_approval_rejection(call):
    data_parts = call.data.split("_")
    action = data_parts[0]
    item_type = data_parts[1]
    user_id = data_parts[2]
    user_name = data_parts[3] if len(data_parts) == 4 else None
    
    if action == "approve":
        bot.send_message(user_id, "<b>Your TMs submission has been approved!</b>", parse_mode="HTML")
        bot.send_message(GROUP_CHAT_ID, f"<b>New TMs added:</b>\n{call.message.text}", parse_mode="HTML")
        cursor.execute("INSERT INTO items (type, name) VALUES (?, ?)", ('tms', user_name))
        conn.commit()
    else:
        bot.send_message(user_id, "<b>Your TMs submission has been rejected.</b>", parse_mode="HTML")
    
    bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)

def get_team_name(message):
    name = message.text
    bot.send_message(message.chat.id, "<b>Provide the members of the team:</b>", parse_mode="HTML")
    bot.register_next_step_handler(message, get_team_members, name)

def get_team_members(message, name):
    members = message.text
    bot.send_message(message.chat.id, "<b>Provide the base stats for the team:</b>", parse_mode="HTML")
    bot.register_next_step_handler(message, get_team_base, name, members)

def get_team_base(message, name, members):
    base = message.text
    user_id = message.from_user.id
    user_name = message.from_user.username

    caption = f"<b>Team Name : </b> {name}\n\n<b>Members : \n\n</b> {members}\n\n<b>Base : </b> {base}\n\n<b>UserID : </b> {user_id}"
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("Approve", callback_data=f"approve_team_{user_id}_{name}_{user_name}"),
               types.InlineKeyboardButton("Reject", callback_data=f"reject_team_{user_id}_{name}"))
    
    auction_message = bot.send_message(ADMIN_CHAT_ID, caption, parse_mode="HTML", reply_markup=markup)
    auction_messages.append(auction_message)

@bot.callback_query_handler(func=lambda call: call.data.startswith(("approve_", "reject_")))
def handle_approval_rejection(call):
    data_parts = call.data.split("_")
    action = data_parts[0]
    item_type = data_parts[1]
    user_id = data_parts[2]
    item_name = data_parts[3]

    user_name = data_parts[4] if len(data_parts) == 5 else None

    user_id = int(user_id)
    
    if item_type == "pokemon":
        if action == "approve":
            bot.send_message(user_id, f"<b>Your Pokemon '{item_name}' has been approved!</b>", parse_mode="HTML")
            bot.send_photo(GROUP_CHAT_ID, call.message.photo[-1].file_id, caption=call.message.caption, parse_mode="HTML")
            cursor.execute("INSERT INTO items (type, name) VALUES (?, ?)", ('pokemon', item_name))
            conn.commit()
        else:
            bot.send_message(user_id, f"<b>Your Pokemon '{item_name}' has been rejected.</b>", parse_mode="HTML")
    elif item_type == "tms":
        if action == "approve":
            bot.send_message(user_id, "<b>Your TMs submission has been approved!</b>", parse_mode="HTML")
            bot.send_message(GROUP_CHAT_ID, f"<b>New TMs added:</b>\n{call.message.text}", parse_mode="HTML")
            cursor.execute("INSERT INTO items (type, name) VALUES (?, ?)", ('tms', item_name))
            conn.commit()
        else:
            bot.send_message(user_id, "<b>Your TMs submission has been rejected.</b>", parse_mode="HTML")
    elif item_type == "team":
        if action == "approve":
            bot.send_message(user_id, f"<b>Your Team '{item_name}' has been approved!</b>", parse_mode="HTML")
            bot.send_message(GROUP_CHAT_ID, f"<b>New Team added:</b>\n{call.message.text}", parse_mode="HTML")
            cursor.execute("INSERT INTO items (type, name) VALUES (?, ?)", ('team', item_name))
            conn.commit()
        else:
            bot.send_message(user_id, f"<b>Your Team '{item_name}' has been rejected.</b>", parse_mode="HTML")
    
    bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)

@bot.message_handler(commands=['current'], func=lambda message: str(message.from_user.id) not in banned_users)
def current_items(message):
    if message.from_user.id not in admin_ids and str(message.from_user.id) not in banned_users:
        bot.reply_to(message, "<b>You are not authorized to use this command.</b>", parse_mode="HTML")
        return

    cursor.execute("SELECT COUNT(*) FROM items WHERE type = 'pokemon'")
    pokemon_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM items WHERE type = 'tms'")
    tms_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM items WHERE type = 'team'")
    teams_count = cursor.fetchone()[0]
    total_count = pokemon_count + tms_count + teams_count
    
    current_message = (
        f"🔹<b>Currently Items In Auction</b> - \n\n"
        f"🔺<b>Pokemon</b> : {pokemon_count} \n"
        f"🔺<b>TMs</b> : {tms_count} \n"
        f"🔺<b>Teams</b> : {teams_count} \n\n"
        f"🔹<b>Total Items</b> :- {total_count} "
    )
    
    bot.reply_to(message, current_message, parse_mode="HTML")

@bot.message_handler(commands=['item'], func=lambda message: str(message.from_user.id) not in banned_users)
def show_item_options(message):
    if message.from_user.id not in admin_ids and str(message.from_user.id) not in banned_users:
        bot.reply_to(message, "<b>You are not authorized to use this command.</b>", parse_mode="HTML")
        return

    markup = types.InlineKeyboardMarkup(row_width=3)
    markup.add(types.InlineKeyboardButton("Pokemon", callback_data="show_pokemon"),
               types.InlineKeyboardButton("TMs", callback_data="show_tms"),
               types.InlineKeyboardButton("Teams", callback_data="show_teams"))
    bot.reply_to(message, "<b>Please Select What you want to see:</b>", parse_mode="HTML", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("show_") and str(call.from_user.id) not in banned_users)
def handle_show_items(call):
    if call.from_user.id not in admin_ids and str(call.from_user.id) not in banned_users:
        bot.reply_to(call.message, "<b>You are not authorized to use this command.</b>", parse_mode="HTML")
        return

    item_type = call.data.split("_")[1].capitalize()
    cursor.execute("SELECT name FROM items WHERE type = ?", (item_type.lower(),))
    items_list = cursor.fetchall()
    
    if items_list:
        items_message = f"<b>Here is the list of {item_type} approved for the next auction:</b>\n\n"
        items_message += "\n".join([f"{i + 1}. {item[0]}" for i, item in enumerate(items_list)])
    else:
        items_message = f"<b>No {item_type} available.</b>"
    
    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=items_message, parse_mode="HTML")

@bot.message_handler(commands=['list'], func=lambda message: str(message.from_user.id) not in banned_users)
def list_all_items(message):
    if message.from_user.id not in admin_ids and str(message.from_user.id) not in banned_users:
        bot.reply_to(message, "<b>You are not authorized to use this command.</b>", parse_mode="HTML")
        return

    cursor.execute("SELECT * FROM items")
    items_list = cursor.fetchall()
    
    if items_list:
        items_message = "<b>Here are the items approved for the next auction:</b>\n\n"
        for i, item in enumerate(items_list):
            items_message += f"{i + 1}. {item[1].capitalize()}: {item[2]}\n"
    else:
        items_message = "<b>No items available.</b>"
    
    bot.reply_to(message, items_message, parse_mode="HTML")

@bot.message_handler(commands=['clear'], func=lambda message: str(message.from_user.id) not in banned_users)
def clear_database(message):
    if message.from_user.id != int(owner_id):
        bot.reply_to(message, "<b>You are not authorized to use this command.</b>", parse_mode="HTML")
        return

    cursor.execute("DELETE FROM items")
    conn.commit()
    bot.reply_to(message, "<b>Database cleared successfully.</b>", parse_mode="HTML")

@bot.message_handler(commands=['next'], func=lambda message: str(message.from_user.id) not in banned_users)
def forward_approved_items(message):
    if message.from_user.id not in admin_ids and str(message.from_user.id) not in banned_users:
        bot.reply_to(message, "<b>You are not authorized to use this command.</b>", parse_mode="HTML")
        return

    if auction_messages:
        auction_message = auction_messages.pop(0)
        bot.forward_message(GROUP_CHAT_ID, auction_message.chat.id, auction_message.message_id)
    else:
        bot.reply_to(message, "<b>No posts to forward.</b>", parse_mode="HTML")


bot.polling(non_stop=True)
