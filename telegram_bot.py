import bot_settings
import logging
import data_manager
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext, CallbackQueryHandler, \
    ConversationHandler

# Set up logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

# set higher logging level for httpx to avoid all GET and POST requests being logged
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

SELECTING_USER_TYPE, SELECTING_LOCATION, CHANGE_LOCATION, REQUESTS, PHONE_NUMBER, UPDATE_PHONE_NUMBER, CHECK_LOCATION = range(
    7)


def start(update, context):
    user_info = update.message.from_user
    user['user_id'] = user_info.id
    user['name'] = user_info.first_name
    logger.info(f"User_id: {user_info.id} User_name: {user_info.first_name} >>>>User_dict: {user}")
    update.message.reply_text(f"Hello {user_info.first_name}! Welcome to our Bot. This is a Bot for good deeds :)")
    # show the location menu
    reply_keyboard = [location_menu]
    update.message.reply_text("Please inform us of your current location",
                              reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True))

    return SELECTING_LOCATION


def select_location(update, context):
    selection = update.message.text
    user["location"] = selection
    logger.info(f"User_location: {selection} >>>>User dict: {user}")
    update.message.reply_text(f"Thanks for the answer.")

    # show_user_type_menu
    reply_keyboard = [user_type_menu]
    update.message.reply_text("what would you like to be?",
                              reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True))

    return SELECTING_USER_TYPE


def select_type(update, context):
    selection = update.message.text
    user["type"] = selection
    logger.info(f"User_type: {selection} >>>>User dict: {user}")
    if selection == user_type_menu[0]:
        update.message.reply_text("I admire your decision to volunteer, that is commendable :)")
        context.user_data['location'] = user['location']
        return check_location(update, context)
    else:
        update.message.reply_text("Please, tell us about your request")
        return REQUESTS


def check_location(update, context):
    if len(context.user_data['location']) > 0:
        users_by_location_list = data_manager.search_users_by_location(str(context.user_data['location']))
        location = 'location'
        logger.info(
            f'number of requests from location {str(context.user_data[location])}is {len(users_by_location_list)}')
    else:
        users_by_location_list = data_manager.search_users_by_location(update.message.text)
        logger.info(
            f'number of requests from location {update.message.text} is {len(users_by_location_list)}')
    if len(users_by_location_list) == 0:
        return no_available_users(update, context)
    else:
        context.user_data['phone'] = [users_by_location_list[i]['phone'] for i in range(len(users_by_location_list))]
        reply_keyboard = [users_by_location_list[i]['request'] for i in range(len(users_by_location_list))]
        update.message.reply_text("Chose one request from the list below?",
                                  reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True))
        return PHONE_NUMBER


def no_available_users(update, context):
    update.message.reply_text("We apologize for the inconvenience, but we currently have no requests in the "
                              "specific location that you chose. However, you can choose another location "
                              "from our available options :)")

    # show_yes_no_menu
    reply_keyboard = [yse_no_menu]
    update.message.reply_text("Do you want to try in another location?",
                              reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True))

    return CHANGE_LOCATION


def change_location(update, context):
    logger.info(f"The choice: {update.message.text}, Type: {type(update.message.text)}")
    if update.message.text == yse_no_menu[0]:
        reply_keyboard = [location_menu]
        update.message.reply_text("Please inform about the new location:",
                                  reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True))
        return CHECK_LOCATION
    else:
        update.message.reply_text("Thanks for your time, try later")
        return ConversationHandler.END


def request_handler(update, context):
    request = update.message.text
    user['request'] = request
    logger.info(f"request: {request} >>>>User_dict: {user}")
    update.message.reply_text("Please write your phone number:)")
    return UPDATE_PHONE_NUMBER


def phone_number(update, context):
    update.message.reply_text(f'here is the number of the request owner {context.user_data["phone"]}')
    return ConversationHandler.END


def update_phone_number(update, context):
    phone = update.message.text
    user['phone'] = phone
    logger.info(f"phone_number: {phone} >>>>User_dict: {user}")
    data_manager.update_users(user)
    update.message.reply_text("A volunteer will call you sooner :)")
    return ConversationHandler.END


def cancel(update, context):
    user_info = update.message.from_user
    update.message.reply_text("Order canceled. Start a new order with /start.")
    user.pop(user_info.id, None)  # Clear the user's order data
    return ConversationHandler.END


user_type_menu = ["VOLUNTEER", "NEED_HELP"]
location_menu = ["EAST", "WEST", 'CENTER']
yse_no_menu = ["YES", "TRY_LATER"]
user = {}


# Main function to run the bot
def main() -> None:
    # Set up the Telegram bot with your token
    updater = Updater(bot_settings.BOT_TOKEN)

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            SELECTING_USER_TYPE: [MessageHandler(Filters.regex("^(VOLUNTEER|NEED_HELP)$"), select_type)],
            SELECTING_LOCATION: [MessageHandler(Filters.regex("^(EAST|WEST|CENTER)$"), select_location)],
            CHANGE_LOCATION: [MessageHandler(Filters.regex("^(YES|TRY_LATER)$"), change_location)],
            REQUESTS: [MessageHandler(Filters.text & ~Filters.command, request_handler)],
            UPDATE_PHONE_NUMBER: [MessageHandler(Filters.text & ~Filters.command, update_phone_number)],
            PHONE_NUMBER: [MessageHandler(Filters.text & ~Filters.command, phone_number)],
            CHECK_LOCATION: [MessageHandler(Filters.text & ~Filters.command, check_location)],

        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    dp.add_handler(conv_handler)

    logger.info("* Start polling...")
    updater.start_polling()  # Starts polling in a background thread.
    updater.idle()  # Wait until Ctrl+C is pressed
    logger.info("* Bye!")


if __name__ == '__main__':
    main()
