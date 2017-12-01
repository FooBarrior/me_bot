import logging.config
import os
import pprint
import site
import traceback
from itertools import islice
from pathlib import Path
from typing import NamedTuple, Dict
from uuid import uuid4

import peewee
import playhouse.fields
from telegram import Bot, Update
from telegram.callbackquery import CallbackQuery
from telegram.ext import Updater
from telegram.ext.callbackqueryhandler import CallbackQueryHandler
from telegram.ext.commandhandler import CommandHandler
from telegram.ext.conversationhandler import ConversationHandler
from telegram.ext.filters import Filters
from telegram.ext.inlinequeryhandler import InlineQueryHandler
from telegram.ext.messagehandler import MessageHandler
from telegram.inline.inlinekeyboardbutton import InlineKeyboardButton
from telegram.inline.inlinekeyboardmarkup import InlineKeyboardMarkup
from telegram.inline.inlinequeryresultarticle import InlineQueryResultArticle
from telegram.inline.inputtextmessagecontent import InputTextMessageContent
from telegram.message import Message
from telegram.parsemode import ParseMode

db = peewee.SqliteDatabase('votes.db')


class Vote(NamedTuple):
    users: list
    text: str


class VoteModel(peewee.Model):
    class Meta:
        database = db
    user_id = peewee.IntegerField()
    msg_id = peewee.IntegerField()
    users = playhouse.fields.PickledField()
    text = peewee.TextField()


db.create_tables([VoteModel], safe=True)

data: Dict[str, Dict[str, Vote]] = {}

token = os.environ['BOT_TOKEN']

updater = Updater(token)

logging.config.dictConfig({
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
        },
    },
    'handlers': {
        "console": {
            "class": "logging.StreamHandler",
            "level": "ERROR",
            "formatter": "standard",
            "stream": "ext://sys.stderr"
        },
    },
    'loggers': {
        '': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': True
        }
    }
})
logger = logging.getLogger(__name__)


def is_site_module(filename: str):
    pkgs = site.getsitepackages()
    for p in pkgs:
        if filename.startswith(p):
            return True
    return False


def error(bot, update: Update, err):
    if update:
        ustr = pprint.pformat(update.to_dict(), width=120)
        logger.exception(f'Update: \n{ustr}')

        message: Message = (update.message
                            or (update.callback_query
                                and update.callback_query.message))
        if message:
            message.reply_text('An error occured. '
                               "We're working it out...")
            if message.from_user.id == 82204126:
                tb = traceback.extract_tb(err.__traceback__)
                for i in 0, -1:
                    while tb and is_site_module(tb[i].filename):
                        tb.pop(i)
                message.reply_text(f"```{''.join(tb.format())}{err}```",
                                   parse_mode=ParseMode.MARKDOWN)
    else:
        logger.exception('Unexpected error!')


updater.dispatcher.add_error_handler(error)


def get_vote_data(user_id, msg_id):
    if user_id in data and msg_id in data[user_id]:
        return data[user_id][msg_id]

    v = VoteModel.filter(user_id=user_id, msg_id=msg_id)
    if v:
        user_data = data.setdefault(user_id, {})
        user_data[msg_id] = Vote(users=v[0].users, text=v[0].text)
        return user_data[msg_id]


def save_vote_data(user_id, msg_id):
    d = dict(user_id=user_id, msg_id=msg_id)
    voters = data[user_id][msg_id]
    defaults = dict(d, text=voters.text, users=voters.users)
    vote, created = VoteModel.get_or_create(defaults=defaults, **d)
    vote.users = voters.users
    vote.save()
    return vote


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
    user_data = data.setdefault(msg.from_user.id, {})
    user_data[res["message_id"]] = Vote(users=[], text=msg.text)
    save_vote_data(msg.from_user.id, res["message_id"])
    return ConversationHandler.END


def get_inline_kb(user_id, msg_id):
    cbdata = f'me#{user_id}#{msg_id}'
    buttons = [[InlineKeyboardButton('Me!',
                                     callback_data=cbdata)]]
    return InlineKeyboardMarkup(buttons)


def on_user_query(bot: Bot, update: Update):
    query: CallbackQuery = update.callback_query
    cmd, *cbdata = query.data.split('#')
    if cmd == 'me':
        user_id, msg_id = map(int, cbdata[:2])
        msg_data: Vote = get_vote_data(user_id, msg_id)
        for u in msg_data.users:
            if u[0].id == query.from_user.id:
                u[0] = query.from_user
                u[1] = not u[1]
                break
        else:
            msg_data.users.append([query.from_user, True])

        save_vote_data(user_id, msg_id)

        t = (f'{"❗" if t else "🖖"}'
             f' {u.first_name or ""} {u.last_name or ""}'
             for u, t, in msg_data.users)

        bot.edit_message_text(text=f'👨‍🚀*{msg_data.text}*\n'
                                   + '-----------------\n'
                                   + '\n'.join(t)
                                   + '\n\n Press "Me!" again, '
                                     'when issue is fixed for you',
                              inline_message_id=query.inline_message_id,
                              reply_markup=get_inline_kb(user_id, msg_id),
                              parse_mode=ParseMode.MARKDOWN)


def on_inline_query(bot, update):
    user_id = update.inline_query.from_user.id
    q: str = update.inline_query.query.lower()
    results = (
        InlineQueryResultArticle(
            id=uuid4(),
            title=v.text,
            input_message_content=InputTextMessageContent(v.text),
            reply_markup=get_inline_kb(user_id, k))
        for k, v in data.get(user_id, {}).items()
        if q in v.text.lower())

    update.inline_query.answer(islice(results, 50),
                               switch_pm_text="Create new vote",
                               switch_pm_parameter='qwe')


conv = ConversationHandler([CommandHandler('new', on_new,
                                           Filters.private)],
                           {1: [MessageHandler(Filters.all,
                                               on_message)]},
                           [])

updater.dispatcher.add_handler(conv)

updater.dispatcher.add_handler(CallbackQueryHandler(on_user_query))
updater.dispatcher.add_handler(InlineQueryHandler(on_inline_query))

updater.start_polling()
updater.idle()
