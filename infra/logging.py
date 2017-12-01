import logging.config
import pprint
import site
import traceback


logger = logging.getLogger(__name__)


def is_site_module(filename: str):
    pkgs = site.getsitepackages()
    for p in pkgs:
        if filename.startswith(p):
            return True
    return False


def error(bot, update, err):
    from telegram import Message, ParseMode

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


def setup_logging():
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

    from infra.updater import updater
    updater.dispatcher.add_error_handler(error)

