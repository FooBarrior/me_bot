from infra.logging import setup_logging


def main():
    from infra.updater import updater
    from controllers import setup_controllers

    setup_controllers()
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    setup_logging()
    main()