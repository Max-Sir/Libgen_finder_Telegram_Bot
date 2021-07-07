import config
import telegram
import telegram.ext
import Channel.channelDB as channelDB
import logging
from Statistics import StatisticsDecorator
from Statistics import SearchInChannelAction
from classes import BotModule


class ChannelModule(BotModule):

    def __init__(self, updater: telegram.ext.Updater, dispatcher: telegram.ext.dispatcher):
        self.updater = updater
        self.dispatcher = dispatcher
        self.tge = telegram.ext  # Алиас для telegram.ext
        self.tg = telegram  # Алиас для telegram

        with channelDB.DBConnect() as _db:
            answer = _db.create_table()
            logging.info("Создание базы - " + str(answer.ok()) + " : error - " + str(answer.error()))

    def install_handlers(self, end_conversation):
        # Алиасы
        filters = self.tge.Filters
        message = self.tge.MessageHandler
        conversation = self.tge.ConversationHandler
        callbackQuery = self.tge.CallbackQueryHandler
        

        # Диалог поиска по каналу
        search_in_channel_conv = conversation(
            entry_points=[
                          message(filters.regex(config.search_in_ch_button) & filters.private, self.send_keyb_for_channel),
                          message(filters.regex(config.prefix_start_in_ch) & filters.private, self.send_keyb_for_channel)
                         ],
            states={
                0: [message(filters.regex(config.back_button) & filters.private, end_conversation),  # Кнопка назад
                    message(filters.regex(config.help_in_fts3_button) & filters.private, self.send_fts3_help),
                    message(filters.text & filters.private, self.search_in_channel)]  # Поиск
            },
            fallbacks=[message(filters.regex(config.back_button), end_conversation)], allow_reentry=True)

        # Отрабатывание на кнопку "Да" в вопросе про продолжение поиска по каналу
        continue_srch_ch_btn = callbackQuery(self.query_continue_search_in_channel, pattern="continue_search")

        self.dispatcher.add_handler(search_in_channel_conv)
        self.dispatcher.add_handler(continue_srch_ch_btn)

    ### Колбеки для поиска на канале
    def send_keyb_for_channel(self, update, context):
        """
        Отправляет кнопки поиска по каналу
        :param update:
        :param context:
        :return:
        """
        keyb = [[config.back_button], [config.help_in_fts3_button]]
        reply_markup = self.tg.ReplyKeyboardMarkup(keyb, resize_keyboard=True, one_time_keyboard=True)
        update.message.reply_text(config.start_in_channel_msg, reply_markup=reply_markup, parse_mode=self.tg.ParseMode.HTML)
        return 0

    def send_fts3_help(self, update, context):
        """
        Отправляет сообщение с описанием возможностей поиска по каналу
        :param update:
        :param context:
        :return:
        """
        update.message.reply_text(config.help_fts3_in_channel, parse_mode=self.tg.ParseMode.HTML)
        return

    @StatisticsDecorator(SearchInChannelAction())
    def search_in_channel(self, update, context):
        """
        После send_keyb_for_channel любое текстовое сообщение отправляется сюда, где используется для поиска по базе канала
        :param update:
        :param context:
        :return:
        """
        if len(update.effective_message.text) > 100 or len(update.effective_message.text) < 2:
            update.message.reply_text("От 2-х до 100 символов")
            return
        self.do_search_channel(context, update.effective_chat.id, update.effective_message.text)

    def query_continue_search_in_channel(self, update, context):
        """
        Метод search_in_channel отправляет кнопку с запросом на продолжения поиска, после ее нажатия - выполняется текущий метод
        :param update:
        :param context:
        :return:
        """
        query = update.callback_query
        context.bot.delete_message(query.message.chat_id, query.message.message_id)
        self.do_search_channel(context, query.message.chat_id)

    @telegram.ext.run_async
    def do_search_channel(self, context, chat_id, text=None, offset_ch=None, limit=config.send_books_limit):
        """
        Поиск по каналу
        Если text не None и offset_ch равно None - Выполняем поиск по тексту со стандартным offset_ch (= 0)
        Если text не None и offset_ch не None - Выполняем поиск по тексту с заданным смещением (offset_ch)
        Если text равен None - Ищем текст в пользовательских данных и выполняем поиск с ним, если не нашли текст - отправляем ошибку
        :param context:
        :param chat_id:
        :param text:
        :param offset_ch:
        :param limit:
        :return:
        """
        if text:
            if not offset_ch:
                offset_ch = 0
        else:
            text = context.user_data.get("last_search_ch", None)
            offset_ch = context.user_data.get("offset_ch", 0)

            if text == None:
                context.bot.send_message(chat_id, "Мы не можем найти твой последний запрос, попробуй еще раз :)")
                return

        with channelDB.Search() as _db:
            data = _db.in_text(text, limit, offset_ch)

        if not data.ok():
            context.bot.send_message(chat_id, data.value())
            return

        for book in data.value():
            try:
                context.bot.forward_message(chat_id, book["channel_id"], book["post_id"])
            except telegram.error.BadRequest as e:
                context.bot.send_message(chat_id, "Мы нашли эту запись, но переслать не смогли, вот всё, что нам известно :)\nt.me/c/{}/{}\n\n{}".format(str(book["channel_id"]).replace("-100", ""), book["post_id"], book["text"]))


        if len(data.value()) == config.send_books_limit:
            keyb = [[self.tg.InlineKeyboardButton("Да", callback_data="continue_search")]]
            reply_markup = self.tg.InlineKeyboardMarkup(keyb)
            context.bot.send_message(chat_id, "Продолжаем поиск?", reply_markup=reply_markup)
            context.user_data["last_search_ch"] = text

        context.user_data["offset_ch"] = offset_ch + limit