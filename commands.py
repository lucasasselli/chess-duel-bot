from shared import app, bot

import logging
from datetime import datetime
import telegram
import constants
from data import UserStatus, User, Match
import humanfriendly
import game
from game import GameResult


class Command(object):

    def __init__(self, user, text, message_id, admin_only=False, status_only=UserStatus.ANY, has_argument=False):

        self.text = text
        self.user = user
        self.message_id = message_id

        self.admin_only = admin_only
        self.status_only = status_only
        self.has_argument = has_argument

    def cmd_body(self):
        pass

    def cmd_run(self, force=False):

        user = self.user

        if self.admin_only and not user.admin:
            # User is not admin
            user.send_message(constants.ERROR_CMD_ADMIN)
        elif int(self.status_only) >= 0 and not user.status == self.status_only and not force:
            # User is not in the correct status
            user.send_message(constants.ERROR_CMD_BAD)
            user.clear_cmd()
        else:
            # Execute command body
            result = self.cmd_body()

            if self.has_argument and result:
                user.set_cmd(self.text[1:])

    def arg_body(self):
        pass

    def arg_run(self):
        self.user.clear_cmd()
        self.arg_body()


##################################################
#                    INIT
##################################################

class Start(Command):

    def __init__(self, user, text, message_id):
        super(Start, self).__init__(user, text, message_id, False, UserStatus.IDLE)

    def cmd_body(self):
        self.user.send_message(constants.CMD_START_STRING)


class New1(Command):

    def __init__(self, user, text, message_id):
        super(New1, self).__init__(user, text, message_id, False, UserStatus.IDLE, True)

    def cmd_body(self):

        user = self.user

        reply_markup = None
        if len(constants.MATCH_TIMEOUTS) > 0:
            custom_keyboard = []
            for timeout in constants.MATCH_TIMEOUTS:
                custom_keyboard.append([timeout])
            reply_markup = telegram.ReplyKeyboardMarkup(custom_keyboard, resize_keyboard=True)

        user.send_message("Please enter the move timeout for the match.", reply_markup=reply_markup)

        return True

    def arg_body(self):

        user = self.user

        timeout = constants.MATCH_TIMEOUTS[self.text]
        if timeout:
            user.send_message("Timeout selected!", reply_markup=telegram.ReplyKeyboardRemove(True))
            user.pending_arg = str(timeout)
            user.put()
            command_handler = New2(user, '/new2', self.message_id)
            command_handler.cmd_run(True)
        else:
            user.send_message(constants.ERROR_BAD_TIMEOUT, reply_markup=telegram.ReplyKeyboardRemove(True))


class New2(Command):

    def __init__(self, user, text, message_id):
        super(New2, self).__init__(user, text, message_id, False, UserStatus.RESERVED, True)

    def cmd_body(self):

        user = self.user

        recent_adversaries = user.recent_adversaries

        reply_markup = None
        if recent_adversaries:
            if len(recent_adversaries) > 0:
                custom_keyboard = []
                for username in recent_adversaries:
                    custom_keyboard.append([username])
                reply_markup = telegram.ReplyKeyboardMarkup(custom_keyboard, resize_keyboard=True)

        user.send_message("Please enter the username of your adversary.", reply_markup=reply_markup)

        return True

    def arg_body(self):

        user = self.user
        adversary_username = self.text

        if adversary_username == user.username and not user.admin:
            user.send_message(constants.ERROR_SAME_USER, reply_markup=telegram.ReplyKeyboardRemove(True))
            return

        query = User.query(User.username == adversary_username)
        query_list = list(query.fetch())

        if len(query_list) != 1:

            # Adversary not found
            invite_button = [[telegram.InlineKeyboardButton("Invite a friend", switch_inline_query=constants.STRING_SHARED)]]
            reply_markup = telegram.InlineKeyboardMarkup(invite_button)
            user.send_message(adversary_username + " is not a Chess Duel Bot user.", reply_markup=telegram.ReplyKeyboardRemove(True))
            user.send_message(constants.STRING_INVITE, reply_markup=reply_markup)

        adversary = query_list[0]
        if adversary.status == UserStatus.IDLE:

            try:
                timeout = int(user.pending_arg)
            except ValueError:
                # TODO: Print error
                return

            match = Match(white_id=adversary.key.id(),
                          black_id=user.key.id(),
                          timeout=timeout)
            match.put()

            # Adversary found
            user.setup_match(match, adversary, False)
            user.send_message(constants.STRING_REQUEST_SENT, reply_markup=telegram.ReplyKeyboardRemove(True))

            adversary.setup_match(match, user, True)
            accept_button = [[telegram.InlineKeyboardButton("Accept", callback_data='/accept'),
                              telegram.InlineKeyboardButton("Refuse", callback_data='/refuse')]]
            reply_markup = telegram.InlineKeyboardMarkup(accept_button)
            adversary.send_message(
                constants.STRING_REQUEST_RECEIVED.format(
                    user.username,
                    humanfriendly.format_timespan(match.timeout)),
                reply_markup=reply_markup)
        else:

            # Adversary busy
            user.send_message("Adversary is busy", reply_markup=telegram.ReplyKeyboardRemove(True))


class AcceptRequest(Command):

    def __init__(self, user, text, message_id):
        super(AcceptRequest, self).__init__(user, text, message_id, False, UserStatus.REQUESTED)

    def cmd_body(self):

        user = self.user
        adversary = user.get_adversary()
        match = user.get_match()

        # Remove inline button
        bot.deleteMessage(user.chat_id, self.message_id)

        # Update last move
        match.last_move_date = datetime.now()
        match.put()

        user.start_match()
        user.send_message("Request accepted!")
        bot.send_photo(user.chat_id, photo=match.get_board_img(user))
        user.send_message("It's your turn!")

        adversary.start_match()
        adversary.send_message(user.username + " has accepted your request.")
        bot.send_photo(adversary.chat_id, photo=match.get_board_img(adversary))
        user.send_message("It's " + user.username + " turn...")


class RefuseRequest(Command):

    def __init__(self, user, text, message_id):
        super(RefuseRequest, self).__init__(user, text, message_id, False, UserStatus.REQUESTED)

    def cmd_body(self):

        user = self.user
        adversary = user.get_adversary()
        match = user.get_match()

        # Remove inline button
        bot.deleteMessage(user.chat_id, self.message_id)

        # Delete match
        match.key.delete()

        # Reset users
        user.reset()
        user.send_message("Request refused!")

        adversary.reset()
        adversary.send_message(user.username + " has refused your request.")


class CancelRequest(Command):

    def __init__(self, user, text, message_id):
        super(CancelRequest, self).__init__(user, text, message_id, False, UserStatus.PENDING)

    def cmd_body(self):

        user = self.user
        adversary = user.get_adversary()

        user.reset()
        user.send_message("Request cancelled!")

        adversary.reset()
        adversary.send_message(user.username + " has cancelled the request.")


##################################################
#                   IN-GAME
##################################################


class Stop(Command):

    def __init__(self, user, text, message_id):
        super(Stop, self).__init__(user, text, message_id, False, UserStatus.PLAYING)

    def cmd_body(self):

        user = self.user
        adversary = user.get_adversary()
        match = user.get_match()

        user.send_message("Game cancelled")
        user.end_game(GameResult.LOSE)

        adversary.send_message(user.username + " has cancelled the game.")
        adversary.end_game(GameResult.WIN)

        # Delete match
        if match:
            match.key.delete()


class Move1(Command):

    def __init__(self, user, text, message_id):
        super(Move1, self).__init__(user, text, message_id, False, UserStatus.PLAYING, True)

    def cmd_body(self):

        user = self.user
        match = user.get_match()

        # Check if it's the user's turn to move
        if match.is_user_turn(user):
            self.user.send_message("Please enter your move, or /cancel.")
            return True
        else:
            self.user.send_message(constants.ERROR_TURN)
            return False

    def arg_body(self):

        user = self.user
        match = user.get_match()
        board = match.get_board()
        # TODO: Check if Null

        if self.text == "/cancel":
            user.send_message("Move cancelled.")
            return

        result = game.check_move(board, self.text)
        if int(result) >= 0:
            user.pending_arg = self.text
            user.put()
            command_handler = Move2(user, '/move2', self.message_id)
            command_handler.cmd_run(True)


class Move2(Command):

    def __init__(self, user, text, message_id):
        super(Move2, self).__init__(user, text, message_id, False, UserStatus.RESERVED, True)

    def cmd_body(self):

        user = self.user
        match = user.get_match()
        board = match.get_board()
        # TODO: Check if Null

        # Check if it's the user's turn to move
        if not match.is_user_turn(user):
            user.send_message(constants.ERROR_TURN)
            return False

        result = game.check_move(board, user.pending_arg)
        if int(result) >= 0:
            accept_button = [[telegram.InlineKeyboardButton("Accept", callback_data='/accept'),
                              telegram.InlineKeyboardButton("Cancel", callback_data='/cancel')]]
            reply_markup = telegram.InlineKeyboardMarkup(accept_button)
            user.send_photo(photo=match.get_board_img(user, user.pending_arg), caption="Do you want to confirm this move?", reply_markup=reply_markup)
            return True
        else:
            user.send_message(constants.ERROR_MOVE_BAD)
            return False

    def arg_body(self):

        user = self.user
        match = user.get_match()

        # Remove inline button
        bot.deleteMessage(user.chat_id, self.message_id)

        if self.text == "/cancel":
            user.send_message("Move cancelled.")
            user.send_photo(photo=match.get_board_img(user))
        elif self.text == "/accept":
            game.move(user, user.pending_arg)


class Chat(Command):

    def __init__(self, user, text, message_id):
        super(Chat, self).__init__(user, text, message_id, False, UserStatus.PLAYING, True)

    def cmd_body(self):

        user = self.user
        adversary = user.get_adversary()

        if user.silence:
            user.send_message(constants.STRING_SILENCE_SELF)
        elif adversary.silence:
            user.send_message(constants.STRING_SILENCE.format(adversary.username))
            return False
        else:
            user.send_message("Please enter your message, or /cancel.")
            return True

    def arg_body(self):

        user = self.user
        adversary = user.get_adversary()

        if self.text:
            if self.text == "/cancel":
                user.send_message("Chat cancelled.")
                return

            msg_string = self.text.strip()
            if len(msg_string) > 0:
                user.send_message("Message sent to " + adversary.username + "!")
                adversary.send_message("_" + user.username + " says:_\n" + msg_string)
                return
        else:
            user.send_message("Message must only contain text!")


class Board(Command):

    def __init__(self, user, text, message_id):
        super(Board, self).__init__(user, text, message_id, False, UserStatus.PLAYING)

    def cmd_body(self):

        user = self.user
        match = user.get_match()

        user.send_photo(photo=match.get_board_img(user))


##################################################
#                  GENERAL
##################################################


class Info(Command):

    def __init__(self, user, text, message_id):
        super(Info, self).__init__(user, text, message_id, False)

    def cmd_body(self):

        user = self.user

        if user.status == UserStatus.PLAYING:
            adversary = user.get_adversary()
            match = user.get_match()
            game_time = int((datetime.now() - match.creation_date).total_seconds())
            move_time = int((datetime.now() - match.last_move_date).total_seconds())

            info_string = constants.STRING_GAME_INFO.format(
                humanfriendly.format_timespan(game_time),
                humanfriendly.format_timespan(match.timeout),
                humanfriendly.format_timespan(move_time),
                match.get_captured(user),
                match.get_captured(adversary),
                user.get_info(),
                adversary.get_info())
        else:
            info_string = user.get_info()

        user.send_message(info_string)


class Silence(Command):

    def __init__(self, user, text, message_id):
        super(Silence, self).__init__(user, text, message_id, False)

    def cmd_body(self):

        user = self.user

        if user.silence:
            # Chat already silent
            user.send_message(constants.ERROR_CHAT_SILENT)
        else:
            # Enable silent chat
            user.silence = True
            user.put()
            user.send_message(constants.STRING_SILENCE_SELF_ON)
            if user.status == UserStatus.PLAYING:
                adversary = user.get_adversary()
                if not adversary.silence:
                    adversary.send_message(constants.STRING_SILENCE_ON.format(user.username))


class Unsilence(Command):

    def __init__(self, user, text, message_id):
        super(Unsilence, self).__init__(user, text, message_id, False)

    def cmd_body(self):
        user = self.user

        if not user.silence:
            # Chat already active
            user.send_message(constants.ERROR_CHAT_NOT_SILENT)
        else:
            # Disable silent chat
            user.silence = False
            user.put()
            user.send_message(constants.STRING_SILENCE_SELF_OFF)
            if user.status == UserStatus.PLAYING:
                adversary = user.get_adversary()
                if not adversary.silence:
                    adversary.send_message(constants.STRING_SILENCE_OFF.format(user.username))


class About(Command):

    def __init__(self, user, text, message_id):
        super(About, self).__init__(user, text, message_id, False)

    def cmd_body(self):
        self.user.send_message(constants.CMD_ABOUT_STRING)


class Help(Command):

    def __init__(self, user, text, message_id):
        super(Help, self).__init__(user, text, message_id, False)

    def cmd_body(self):
        self.user.send_message(constants.CMD_HELP_STRING)


##################################################
#                   ADMIN
##################################################

class Admin(Command):

    def __init__(self, user, text, message_id):
        super(Admin, self).__init__(user, text, message_id, False, UserStatus.ANY, True)

    def cmd_body(self):
        if not self.user.admin:
            self.user.send_message("Please enter the password, or /cancel.")
            return True
        else:
            self.user.send_message("You are already an admin!")
            return False

    def arg_body(self):

        user = self.user

        if self.text:
            if self.text == "/cancel":
                user.send_message("Command cancelled.")
                return
            elif self.text == app.config["ADMIN_PASS"]:
                user.admin = True
                user.put()
                user.send_message("User promoted to admin!")
        else:
            user.send_message(constants.ERROR_BAD_INPUT_GENERAL)


cmd_classes = {
    'start': Start,
    'new': New1,
    'new2': New2,
    'stop': Stop,
    'move': Move1,
    'move2': Move2,
    'chat': Chat,
    'board': Board,
    'accept': AcceptRequest,
    'refuse': RefuseRequest,
    'cancel': CancelRequest,
    'info': Info,
    'silence': Silence,
    'unsilence': Unsilence,
    'about': About,
    'help': Help,
    'admin': Admin,
}


def handle_input(user, text, message_id):

    # Text must always exist
    if not text:
        logging.debug("User %s has sent an empty message", user.username)
        user.clear_cmd()
        return

    if user.pending_cmd:
        # The user has a pending command, parse text as argmument
        logging.debug("Argument \"%s\" received from user %s", text, user.username)

        command = user.pending_cmd

        if command in cmd_classes:
            command_handler = cmd_classes[command](user, text, message_id)
            command_handler.arg_run()
        else:
            user.send_message(constants.ERROR_CMD_UNKNOWN)
            user.clear_cmd()

    elif text[0] == "/":
        # Input begins with a slash, parse text as a command
        command = text[1:]
        logging.debug("Command \"%s\" received from user %s", command, user.username)

        if command in cmd_classes:
            command_handler = cmd_classes[command](user, text, message_id)
            command_handler.cmd_run()
        else:
            user.send_message(constants.ERROR_CMD_UNKNOWN)
            user.clear_cmd()

    elif user.status == UserStatus.PLAYING:
        # If the user is playing, assume this as a move command
        match = user.get_match()
        if match:
            game.move(user, text)
    else:
        user.send_message(constants.ERROR_BAD_INPUT_GENERAL)
