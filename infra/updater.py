import os

from telegram.ext import Updater

token = os.environ['BOT_TOKEN']

updater = Updater(token)
