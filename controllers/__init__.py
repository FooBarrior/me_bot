from telegram.ext import CallbackQueryHandler, InlineQueryHandler

from controllers.chat_query import on_user_query, on_inline_query
from infra.updater import updater
from .create import cmd_new


def setup_controllers():
    updater.dispatcher.add_handler(cmd_new)

    updater.dispatcher.add_handler(CallbackQueryHandler(on_user_query))
    updater.dispatcher.add_handler(InlineQueryHandler(on_inline_query))