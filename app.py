# from pocket import Pocket, PocketException
import urlextractor
from ForwardBotDatabase import ForwardBotDatabase
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
import logging
import tokens
from pocket import Pocket, PocketException

from flask import Flask

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO)

logger = logging.getLogger(__name__)
pocket_instance = Pocket(tokens.POCKET_CONSUMER_TOKEN, tokens.POCKET_ACCESS_TOKEN)
auth_token = ""
db = ForwardBotDatabase('botusers.db')
app = Flask(__name__)

users = {}


def start(bot, update, args):
    telegram_user = update.message.from_user

    if len(args) > 0:
        try:
            access_token = pocket_instance.get_access_token(tokens.POCKET_CONSUMER_TOKEN, args[0])
        except PocketException:
            bot.sendMessage(update.message.chat_id, text="Authorization error. \n Please, try again.")
            authorize_bot(bot, update)

        if access_token:
            db.update_user(telegram_user, access_token)
            auth_token = access_token
            pocket_instance.access_token(auth_token)
            print "Access token: " + access_token
            bot.sendMessage(update.message.chat_id, text="Bot was successfully authorized!" \
                                                         "Now you can start sharing messages with URLs")
        else:
            bot.sendMessage(update.message.chat_id, text="Authorization was unsuccessful!" \
                                                         "Please, try once more")
            authorize_bot(bot, update)

    else:
        db_user = db.get_user_details(telegram_user.id)
        if db_user:
            if db_user['auth_token']:
                pocket_instance.access_token(db_user['auth_token'])
                bot.sendMessage(update.message.chat_id, text="Welcome back, " + telegram_user.first_name + "!")
        else:
            authorize_bot(bot, update)


def help(bot, update):
    bot.sendMessage(update.message.chat_id, text="Help!")


def messages(bot, update):
    telegram_user = update.message.from_user

    if not users.has_key(telegram_user.id):
        authorize_bot(bot, update)
    elif (users.has_key(telegram_user.id)) and (len(users[telegram_user.id]['auth_token']) > 0):
        global auth_token
        auth_token = users[telegram_user.id]['auth_token']
        pocket_instance.access_token(auth_token)
        urls = urlextractor.parsetext(update.message.text)
        if len(urls) > 0:
            response = pocket_push(urls)
            message_text = "Added:\n"
            i = 1
            print response
            for item in response:
                message_text += str(i) + ". " + item["item"]["title"] + "\n"
                i += 1
            print message_text
            bot.sendMessage(update.message.chat_id, text=message_text)
        else:
            bot.sendMessage(update.message.chat_id, text="No URLs found!")


    else:
        authorize_bot(bot, update)


def error(bot, update, error):
    logger.warn('Update "%s" caused error "%s"' % (update, error))


def authorize_bot(bot, update):
    telegram_user = update.message.from_user
    users[telegram_user.id] = telegram_user
    db.add_user(telegram_user)

    print "checking request token"
    request_token = pocket_instance.get_request_token(tokens.POCKET_CONSUMER_TOKEN,
                                                      "https://telegram.me/links_forward_bot")
    print request_token
    auth_url = pocket_instance.get_auth_url(request_token,
                                            "https://telegram.me/links_forward_bot?start=" + request_token)
    linkButton = [[InlineKeyboardButton("Authorize bot", url=auth_url)]]

    bot.sendMessage(update.message.chat_id, text="You need to authorize this bot for your Pocket account",
                    reply_markup=InlineKeyboardMarkup(linkButton),
                    disable_web_page_preview=True)


def pocket_push(urls):
    responses = []
    print urls
    for url in urls:
        print ("Sending URL: " + url)
        try:
            responses.append(pocket_instance.add(url))
        except PocketException as e:
            #TODO Add error messages to user
            print(e.message)
    return responses


def main():
    global users
    users = db.get_users()

    print users

    updater = Updater(tokens.TELEGRAM_TOKEN)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler('start', start, pass_args=True))
    dp.add_handler(CommandHandler("help", help))
    dp.add_handler(MessageHandler([Filters.text], messages))

    dp.add_error_handler(error)

    updater.start_polling()

    updater.idle()


@app.route('/')
def hello_world():
    return 'Hello World!'


if __name__ == '__main__':
    main()
