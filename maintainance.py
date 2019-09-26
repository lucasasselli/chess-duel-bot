import humanfriendly
import logging
from data import User, Match, GameResult
import constants


def task_users():

    logging.info("Performing user maintainance...")

    # Delete all users whose last move is older than USER_TIMEOUT
    query = User.query(User.expired == True)
    query_list = list(query.fetch())

    for user in query_list:
        logging.info("Deleting user %s. Last activity: %s", user.username, str(user.last_activity_date))
        user.key.delete()


def task_matches():

    logging.info("Performing match maintainance...")

    # Delete all matches whose last move is older than the specified timeout
    query = Match.query(Match.expired == True)
    query_list = list(query.fetch())

    for match in query_list:

        logging.info("Deleting match %s. Last activity: %s", match.key.id(), str(match.last_move_date))

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
        match.key.delete()
