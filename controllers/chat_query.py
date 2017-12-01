from itertools import islice
from uuid import uuid4

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Bot, Update, CallbackQuery, ParseMode, \
    InlineQueryResultArticle, InputTextMessageContent
from telegram.ext import CallbackQueryHandler, InlineQueryHandler

from entities import Vote
from infra.updater import updater
from storage import get_vote_data, save_vote_data, get_user_data


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
        for k, v in get_user_data(user_id).items()
        if q in v.text.lower())

    update.inline_query.answer(islice(results, 50),
                               switch_pm_text="Create new vote",
                               switch_pm_parameter='qwe')
