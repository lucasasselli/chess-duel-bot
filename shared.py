import flask
import telegram

import google.cloud.logging
import google.cloud.ndb


def ndb_wsgi_middleware(wsgi_app):
    def middleware(environ, start_response):
        with ndb_client.context():
            return wsgi_app(environ, start_response)

    return middleware


ndb_client = google.cloud.ndb.Client()

log_client = google.cloud.logging.Client()
log_client.setup_logging()

global app
app = flask.Flask(__name__)
app.config.from_pyfile('main.cfg', silent=True)
app.wsgi_app = ndb_wsgi_middleware(app.wsgi_app)

global bot
bot = telegram.Bot(token=app.config['BOT_TOKEN'])
