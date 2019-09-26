import constants
import chess

from enum import IntEnum


class GameResult(IntEnum):
    LOSE = -1
    DRAW = 0
    WIN = 1


class MoveResult(IntEnum):
    UNKNOWN = -2
    BAD = -1
    GOOD = 0
    CHECK = 1
    CHECKMATE = 2
    STALEMATE = 3


def parse_move(move_code):
    try:
        move_code = move_code.lower().replace(" ", "")
        return chess.Move.from_uci(move_code)
    except (ValueError, AttributeError):
        return None


def check_move(board, move_code):

    chess_move = parse_move(move_code)

    dummy = board.copy()

    if not chess_move:
        return MoveResult.UNKNOWN

    if chess_move in board.legal_moves:

        dummy.push(chess_move)

        if dummy.is_checkmate():
            return MoveResult.CHECKMATE
        elif dummy.is_check():
            return MoveResult.CHECK
        elif dummy.is_stalemate():
            return MoveResult.STALEMATE
        else:
            return MoveResult.GOOD
    else:
        return MoveResult.BAD


def move(user, move_code):

    adversary = user.get_adversary()
    match = user.get_match()
    # TODO: Check if Null

    # Check if it's the user's turn to move
    if not match.is_user_turn(user):
        user.send_message(constants.ERROR_TURN)
        return

    move_result = match.move(move_code)

    if int(move_result) >= 0:

        user.send_photo(photo=match.get_board_img(user))
        adversary.send_photo(
            photo=match.get_board_img(adversary),
            caption=user.username + " responded!")

        if move_result == MoveResult.CHECKMATE:

            # User wins!
            user.end_game(GameResult.WIN)
            user.send_message(constants.STRING_GAME_CHECKMATE_WIN)
            user.send_message(constants.STRING_GAME_END)

            # Adversary lose!
            adversary.end_game(GameResult.LOSE)
            adversary.send_message(
                constants.STRING_GAME_CHECKMATE_LOSE.format(user.username))
            adversary.send_message(constants.STRING_GAME_END)

            # Delete match
            if match:
                match.key.delete()

        elif move_result == MoveResult.STALEMATE:

            # Stale mate
            user.send_message(constants.STRING_GAME_STALEMATE)
            user.end_game(GameResult.DRAW)
            adversary.send_message(constants.STRING_GAME_STALEMATE)
            adversary.end_game(GameResult.DRAW)

            # Delete match
            if match:
                match.key.delete()

        else:

            if move_result == MoveResult.CHECK:
                user.send_message(constants.STRING_GAME_CHECK)
                adversary.send_message(constants.STRING_GAME_CHECK)

            user.send_message(
                constants.STRING_GAME_TURN_WAIT.format(adversary.username))
            adversary.send_message(constants.STRING_GAME_TURN_YOUR)
    else:
        # Error
        if move_result == MoveResult.BAD:
            user.send_message(constants.ERROR_MOVE_BAD)
        elif move_result == MoveResult.UNKNOWN:
            user.send_message(constants.ERROR_MOVE_UNKNOWN)
