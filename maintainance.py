from shared import app

import humanfriendly
import logging
from data import User, Match, GameResult
import constants
from datetime import datetime, timedelta


def task_users():

    logging.info("Performing user maintainance...")

    users = list(User.query().fetch())

    for user in users:
        # Delete all users whose last move is older than USER_TIMEOUT
        expired = (datetime.now() - user.last_activity_date) > timedelta(days=app.config['USER_TIMEOUT'])
        if expired:
            # Delete user
            logging.info("Deleting user %s. Last activity: %s", user.username, str(user.last_activity_date))
            user.key.delete()


def task_matches():

    logging.info("Performing match maintainance...")

    matches = list(Match.query().fetch())

    for match in matches:

        # Delete all matches whose last move is older than the specified timeout
        if match.last_move_date:
            expired = (datetime.now() - match.last_move_date) > timedelta(seconds=match.timeout)
        else:
            expired = False

        if expired:

            white = User.get_by_id(match.white_id)
            black = User.get_by_id(match.black_id)

            if match.is_user_turn(white):
                looser = white
                winner = black
            else:
                winner = white
                looser = black

            white.send_message(constants.ERROR_TIMEOUT.format(
                looser.username,
                humanfriendly.format_timespan(match.timeout)))
            black.send_message(constants.ERROR_TIMEOUT.format(
                looser.username,
                humanfriendly.format_timespan(match.timeout)))

            winner.end_game(GameResult.WIN)
            looser.end_game(GameResult.LOSE)

            # Delete match
            logging.info("Deleting match %s. Last activity: %s", match.key.id(), str(match.last_move_date))
            match.key.delete()


def notify_admins(message):

    admins = list(User.query(User.admin == True).fetch())

    for admin in admins:
        admin.send_message(message)