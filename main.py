from shared import app, bot

from datetime import datetime
import logging
import flask
import telegram
import constants
from data import User
import commands
from maintainance import task_users, task_matches


@app.route(app.config['BOT_HOOK'], methods=['POST'])
def webhook_handler():
    if flask.request.method == "POST":

        # Retrieve the message in JSON and then transform it to Telegram object
        update = telegram.Update.de_json(flask.request.get_json(force=True), bot)

        if update.message:
            # Regular message
            text = update.message.text
            user_id = update.message.from_user.id
            chat_id = update.message.chat_id
            username = update.message.from_user.username
            message_id = None
        elif update.callback_query:
            # Callback query
            text = update.callback_query.data
            user_id = update.callback_query.from_user.id
            chat_id = update.callback_query.message.chat_id
            username = update.callback_query.from_user.username
            message_id = update.callback_query.message.message_id
        else:
            logging.error("Received unknown update!")
            return constants.RESPONSE_OK

        # User must have username
        if not username:
            bot.sendMessage(chat_id, constants.ERROR_NO_USERNAME)
            return constants.RESPONSE_OK

        # Retrieve/Create user
        user = User.get_by_id(user_id)
        if not user:
            # New user
            logging.info("User %s not found! Creating new user...", user_id)
            user = User(id=user_id, chat_id=chat_id, username=username)
            user.put()
        else:
            # Existing user
            user.last_activity_date = datetime.now()
            if username != user.username:
                logging.debug("User %s has changed username from %s to %s", user_id, user.username, username)
                user.username = username
            user.put()

        commands.handle_input(user, text, message_id)

        return constants.RESPONSE_OK


@app.route('/set_webhook', methods=['GET', 'POST'])
def set_webhook():

    hostname = app.config['BOT_HOST']
    webhook = 'https://' + hostname + app.config['BOT_HOOK']

    logging.info("Setting bot webhook at %s", webhook)

    s = bot.setWebhook(webhook)
    if s:
        return constants.RESPONSE_OK
    else:
        return constants.RESPONSE_FAIL


@app.route('/tasks/maintain_users', methods=['GET', 'POST'])
def maintain_users():
    task_users()
    return constants.RESPONSE_OK


@app.route('/tasks/maintain_matches', methods=['GET', 'POST'])
def maintain_matches():
    task_matches()
    return constants.RESPONSE_OK


@app.route('/')
def index():
    return constants.RESPONSE_OK
