from telegram import Bot, Update, Message, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ConversationHandler, CommandHandler, MessageHandler, Filters

from entities import Vote
from infra.updater import updater
from storage import get_user_data, save_vote_data


def on_new(bot: Bot, update: Update):
    msg: Message = update.message
    msg.reply_text('Enter your comment')
    return 1


def on_message(bot: Bot, update: Update):
    msg: Message = update.message
    buttons = [[InlineKeyboardButton('test', callback_data='test'),
                InlineKeyboardButton('send', switch_inline_query='')]]
    res = msg.reply_text(msg.text,
                         reply_markup=InlineKeyboardMarkup(buttons))
    user_data = get_user_data(msg.from_user.id)
    user_data[res["message_id"]] = Vote(users=[], text=msg.text)
    save_vote_data(msg.from_user.id, res["message_id"])
    return ConversationHandler.END


cmd_new = ConversationHandler([CommandHandler('new', on_new,
                                              Filters.private)],
                             {1: [MessageHandler(Filters.all,
                                                 on_message)]},
                             [])
