import config
import telegram.ext
import telegram
import logging

from Channel import ChannelModule
from Libgen import LibgenModule
from Channel import ChannelModuleAdmin
from Supporting import OfferBookModule
from Statistics import StatisticsModule

from Statistics import StatisticsDecorator
from Statistics import StartAction
from Statistics import MainMenuAction
import Statistics.statisticsDB

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.DEBUG)

class MainBot(object):

    def __init__(self, token, request_kwargs=dict):
        self.updater = telegram.ext.Updater(token=token, use_context=True, request_kwargs=request_kwargs)
        self.dispatcher = self.updater.dispatcher
        self.tge = telegram.ext  # Алиас для telegram.ext
        self.tg = telegram  # Алиас для telegram

        self.channelModule = ChannelModule(self.updater, self.dispatcher)
        self.channelModuleAdmin = ChannelModuleAdmin(self.updater, self.dispatcher)
        self.libgenModule = LibgenModule(self.updater, self.dispatcher)
        self.offerBookModule = OfferBookModule(self.updater, self.dispatcher)
        self.statisticsModule = StatisticsModule(self.updater, self.dispatcher)

        self.__set_all_handlers()

    def __set_all_handlers(self):
        self.channelModule.install_handlers(self.__end_conversation)
        self.channelModuleAdmin.install_handlers(self.__end_conversation)
        self.libgenModule.install_handlers(self.__end_conversation)
        self.statisticsModule.install_handlers(self.__end_conversation)
        self.offerBookModule.install_handlers(self.__end_conversation)

        self.__set_other_handlers()

    def __set_other_handlers(self):
        """
        Устанавливает всякие мелкие хендлеры, вроде отрабатывание на "старт" и т.п.
        :return:
        """
        # Алиасы
        filters = self.tge.Filters
        message = self.tge.MessageHandler
        command = self.tge.CommandHandler

        # Отрабатывание на простой start
        start_handler = command('start', self.__send_start_msg, filters=filters.private)
        # Отрабатывание на любое сообщение, необходимо в случае перезагрузке бота (когда потерялись диалоги выше)
        back_button_handl = message(filters.all & filters.private, self.__send_main_menu)

        self.dispatcher.add_handler(start_handler)
        self.dispatcher.add_handler(back_button_handl)

    def __close_all_conversation_handler(self, update):
        """
        Проходит по всем разговорным хендлерам и закрывает их, грязный хак
        :param update:
        :return:
        """
        all_hand = self.dispatcher.handlers
        for dict_group in all_hand:
            for handler in all_hand[dict_group]:
                if isinstance(handler, self.tge.ConversationHandler):
                    handler.update_state(self.tge.ConversationHandler.END, handler._get_key(update))

        return self.tge.ConversationHandler.END

    def __end_conversation(self, update, context):
        """
        Просто завершает любой диалог и топает в главное меню
        :param update:
        :param context:
        :return:
        """

        self.__send_main_menu(update, context)
        return self.tge.ConversationHandler.END

    def start(self):
        self.updater.start_polling()

    @StatisticsDecorator(MainMenuAction())
    def __send_main_menu(self, update, context):
        if update.effective_user.id == config.admin:
            keyb = config.start_admin_reply_markup
        else:
            keyb = config.start_reply_markup

        reply_markup = self.tg.ReplyKeyboardMarkup(keyb, resize_keyboard=True, one_time_keyboard=True)
        context.bot.send_message(update.effective_user.id, config.main_menu_msg, reply_markup=reply_markup)

        # Дергаем закрытие всех разговорных хендлеров, не помню точно, какой баг это лечило,
        # кажется была проблема с переходом из одного разговора в другой
        self.__close_all_conversation_handler(update)

        return self.tge.ConversationHandler.END

    @StatisticsDecorator(StartAction())
    def __send_start_msg(self, update, context):
        """
        Отрабатывает на простой start
        :param update:
        :param context:
        :return:
        """
        update.message.reply_text(config.start_message, parse_mode=self.tg.ParseMode.HTML)
        self.__send_main_menu(update, context)


with Statistics.statisticsDB.DBConnect() as _db:
    # Дергаем метод базы статистики, для инициализации самой базы
    _db.create_table()

chatbot = MainBot(config.token, config.REQUEST_KWARGS)
chatbot.start()