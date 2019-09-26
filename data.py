from shared import bot

import io
import logging
from datetime import datetime
from enum import IntEnum
from google.cloud import ndb
import telegram
import emoji
import chess
import chess.svg
import cairosvg
import constants
import game
from game import GameResult


class UserStatus(IntEnum):
    ANY = -1
    IDLE = 0
    PENDING = 1
    REQUESTED = 2
    PLAYING = 3
    RESERVED = 99


class User(ndb.Model):

    # User informations
    username = ndb.StringProperty()
    chat_id = ndb.IntegerProperty()
    sign_up_date = ndb.DateTimeProperty(default=datetime.now())
    last_activity_date = ndb.DateTimeProperty(default=datetime.now())
    recent_adversaries = ndb.StringProperty(repeated=True)
    win_count = ndb.IntegerProperty(default=0)
    loss_count = ndb.IntegerProperty(default=0)

    # Command parser
    pending_cmd = ndb.StringProperty(default=None)
    pending_arg = ndb.StringProperty(default=None)

    # Game
    status = ndb.IntegerProperty(default=UserStatus.IDLE)
    adversary_id = ndb.IntegerProperty()
    match_id = ndb.IntegerProperty()
    silence = ndb.BooleanProperty(default=False)

    # Properties
    admin = ndb.BooleanProperty(default=False)

    def reset(self):
        self.match_id = None
        self.adversary = None
        self.status = UserStatus.IDLE
        self.put()

    def set_cmd(self, cmd):
        self.pending_cmd = cmd
        self.put()

    def clear_cmd(self):
        self.pending_cmd = None
        self.put()

    def get_adversary(self):
        if self.adversary_id:
            adversary = User.get_by_id(self.adversary_id)
            if not adversary:
                logging.error("Unable to find adversary with id %d", self.adversary_id)
                self.reset()
                return None
            else:
                return adversary
        else:
            logging.error("adversary_id is not set for user %d.", self.key.id)
            return None

    def setup_match(self, match, adversary, invited):

        self.match_id = match.key.id()

        self.adversary_id = adversary.key.id()

        if invited:
            self.status = UserStatus.REQUESTED
        else:
            self.status = UserStatus.PENDING

        # Recent
        if self.recent_adversaries:
            if adversary.username not in self.recent_adversaries:
                self.recent_adversaries.append(adversary.username)
                if len(self.recent_adversaries) > 3:
                    self.recent_adversaries = self.recent_adversaries[1:]
        else:
            self.recent_adversaries = [adversary.username]

        self.put()

    def start_match(self):
        self.status = UserStatus.PLAYING
        self.put()

    def get_match(self):
        if self.match_id:
            match = Match.get_by_id(self.match_id)
            if not match:
                logging.error("Unable to find match with id %d", self.match_id)
                # TODO: Reset user and adversary
                return None
            else:
                return match
        else:
            logging.error("match_id is not set for user %d.", self.key.id)
            return None

    def get_info(self):
        return constants.STRING_USER_INFO.format(
            self.username,
            str(self.win_count),
            str(self.loss_count),
            self.sign_up_date.strftime("%B %Y"))

    def end_game(self, result):
        if result == GameResult.WIN:
            self.win_count += 1
        elif result == GameResult.LOSE:
            self.loss_count += 1
        else:
            pass

        self.reset()

    def send_message(self, text, parse_mode=None, disable_web_page_preview=True, disable_notification=False, reply_to_message_id=None, reply_markup=None, timeout=None, **kwargs):

        emoji_text = emoji.emojize(text, use_aliases=True)

        bot.send_message(self.chat_id,
                         emoji_text,
                         parse_mode=telegram.ParseMode.MARKDOWN,
                         disable_web_page_preview=disable_web_page_preview,
                         disable_notification=disable_notification,
                         reply_to_message_id=reply_to_message_id,
                         reply_markup=reply_markup,
                         timeout=timeout,
                         **kwargs)

    def send_photo(self, photo, caption=None, disable_notification=True, reply_to_message_id=None, reply_markup=None, timeout=20, **kwargs):

        if caption:
            emoji_text = emoji.emojize(caption, use_aliases=True)
        else:
            emoji_text = None

        bot.send_photo(self.chat_id,
                       photo,
                       caption=emoji_text,
                       disable_notification=disable_notification,
                       reply_to_message_id=reply_to_message_id,
                       reply_markup=reply_markup,
                       timeout=timeout,
                       parse_mode=telegram.ParseMode.MARKDOWN,
                       **kwargs)


class Match(ndb.Model):

    creation_date = ndb.DateTimeProperty(default=datetime.now())

    fen = ndb.StringProperty(default=chess.Board().fen())

    white_id = ndb.IntegerProperty()
    black_id = ndb.IntegerProperty()

    last_move_code = ndb.StringProperty()
    last_move_date = ndb.DateTimeProperty(default=None)
    timeout = ndb.IntegerProperty(default=3600)

    def get_board(self):

        return chess.Board(self.fen)

    def move(self, move_code):

        board = self.get_board()

        result = game.check_move(board, move_code)
        chess_move = game.parse_move(move_code)
        if int(result) >= 0:

            board.push(chess_move)
            self.fen = board.fen()
            self.last_move_code = move_code
            self.last_move_date = datetime.now()
            self.put()

        return result

    def get_color(self, user):
        if user.key.id() == self.white_id:
            return chess.WHITE
        elif user.key.id() == self.black_id:
            return chess.BLACK
        else:
            return None

    def is_user_turn(self, user):

        board = self.get_board()

        if user.key.id() == self.white_id == self.black_id:
            # If the user is both the black and white user
            return True
        else:
            return (board.turn == self.get_color(user))

    def get_board_img(self, user, preview_move=None):

        board = self.get_board()

        if not preview_move:
            move = game.parse_move(self.last_move_code)
        else:
            move = game.parse_move(preview_move)
            board.push(move)

        # Generate SVG
        if user.key.id() == self.black_id:
            svg_string = chess.svg.board(
                board=board,
                flipped=True,
                lastmove=move)
        else:
            svg_string = chess.svg.board(
                board=board,
                flipped=False,
                lastmove=move)

        # Convert SVG to PNG
        mem_file = io.BytesIO()
        cairosvg.svg2png(svg_string, write_to=mem_file)
        mem_file.seek(0)

        return mem_file

    def get_captured(self, user):

        color = not(self.get_color(user))

        dummy = chess.Board()
        board = self.get_board()

        output = ""

        for piece_type in range(1, 7):
            dummy_count = len(dummy.pieces(piece_type, color))
            board_count = len(board.pieces(piece_type, color))
            delta = dummy_count - board_count
            output += delta*chess.Piece(piece_type, color).unicode_symbol()

        return output
