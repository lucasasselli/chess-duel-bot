# Command messages
CMD_START_STRING = """\
Welcome to Chess Duel Bot! Use /new to start a new game, or /help for the \
complete guide.
"""

CMD_ABOUT_STRING = """\
Created with love by @LucaSasselli :heart:

You can make a donation to Chess Duel Bot at this [link](https://paypal.me/lucasasselli).

Money from donations will be used to pay the server, help the development of \
new features and maybe pay a few beers! :beers:
"""

CMD_HELP_STRING = """\
To start a new game enter /new. You can only play one match at the time.

Chess Duel Bot uses a _From-To coordinate notation_ for moves \
(e.g. e2e4, e7e8q for promotion to Queen). While in game you \
can move the pieces with the /move command to preview the \
move, or by simply typing the coordinates. 

*General*:

/new - Start a new game

*In-Game:*
/chat - Chat with the adversary
/move - Move a piece
/board - Show the board
/stop - Cancel the current game

*General:*
/info - Show user/game information
/silence - Silence the chat
/unsilence - Unsilence the chat
/about - Show info on this bot
/help - Show this help message
"""

# Other strings
STRING_REQUEST_SENT = "Request sent! Enter /cancel to cancel the request."
STRING_REQUEST_RECEIVED = "{} has requested a game with {} move timeout. Do you want to accept?"

STRING_INVITE = "Can't find a friend on Chess Duel Bot? :cry: Send him/her an invite! :muscle:"
STRING_SHARED = "Join me for a chess game!"

STRING_SILENCE = "{} doesn't want to be bothered."
STRING_SILENCE_SELF = "You silenced the chat! To re-enable it use /unsilence."
STRING_SILENCE_SELF_ON = "You silenced the chat! To re-enable it use /unsilence."
STRING_SILENCE_SELF_OFF = "You unsilenced the chat!"
STRING_SILENCE_ON = "{} has silenced the chat!"
STRING_SILENCE_OFF = "{} has unsilenced the chat!"

STRING_USER_INFO = """\
*{}:*
Wins: _{}_
Losses: _{}_
User since: _{}_
"""

STRING_GAME_TURN_YOUR = "It's your turn!"
STRING_GAME_TURN_WAIT = "It's {} turn..."
STRING_GAME_STALEMATE = "Stalemate!"
STRING_GAME_CHECK = "Check! :grimacing:"
STRING_GAME_CHECKMATE_WIN = "Checkmate! You win! :sunglasses:"
STRING_GAME_CHECKMATE_LOSE = "Checkmate! {} wins the game! :cry:"
STRING_GAME_END = """\
Did you enjoy the game? Do you like this bot? Then consider donating to Chess Duel Bot at this [link](https://paypal.me/lucasasselli).

Money from donations will be used to pay the server, help the development of new features and maybe pay a few beers! :beers:
"""


STRING_GAME_INFO = """\
*Game:*
Game Time: _{}_
Move Timeout: _{}_
Last move: _{} ago_
{}
{}

{}

{}
"""

# Error messages
ERROR_CMD_ADMIN = "You must be admin to run thim command!"
ERROR_CMD_UNKNOWN = "Unknown command!"
ERROR_CMD_BAD = "Invalid command!"
ERROR_NO_USERNAME = """\
In order to play Chess Duel Bot you must set a Telegram username.
More info at this [link](https://telegram.org/faq#q-what-are-usernames-how-do-i-get-one)."""
ERROR_MOVE_BAD = "You can't do this move!"
ERROR_MOVE_UNKNOWN = "Sorry, I don't understand this move!"
ERROR_TURN = "It's not your turn!"
ERROR_CHAT_SILENT = "Chat is already silent!"
ERROR_CHAT_NOT_SILENT = "Chat is already active!"
ERROR_BAD_INPUT_GENERAL = "Unknown input. Do you need /help?"
ERROR_SAME_USER = "You can't play a game against yourself!"
ERROR_TIMEOUT = "Timeout! User {} failed to move in {}."
ERROR_BAD_TIMEOUT = "Invalid timeout!"

# HTTP responses
RESPONSE_OK = "OK"
RESPONSE_FAIL = "FAIL"

# Game
MATCH_TIMEOUTS = {
        "10 Minutes": 10*60,
        "30 Minutes": 30*60,
        "1 Hour": 1*3600,
        "6 Hours": 6*3600,
        "12 Hours": 12*3600,
        "1 Day": 24*3600,
        "2 Days": 2*24*3600,
        "1 Week": 7*24*3600
}
